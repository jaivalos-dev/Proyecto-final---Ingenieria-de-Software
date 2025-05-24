from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponse
import decimal
import datetime
from .utils import generar_reporte_nomina
from django.db import connection
from .models import Empleado, Nomina, Deduccion, TipoNomina, Departamento, Estado, Puesto
from .forms_nomina import GenerarNominaForm, EmpleadoNominaFormSet, FiltroNominaForm
from .decorators import admin_required, empleado_required, admin_or_empleado_required

@admin_required
def nomina_list(request):
    """Vista para listar todas las nóminas generadas"""
    # Formulario de filtro
    filtro_form = FiltroNominaForm(request.GET or None)
    
    # Obtener todas las nóminas ordenadas por fecha de generación descendente
    nominas = Nomina.objects.all().order_by('-fecha_generacion')
    
    # Aplicar filtros si el formulario es válido
    if filtro_form.is_valid():
        fecha_desde = filtro_form.cleaned_data.get('fecha_desde')
        fecha_hasta = filtro_form.cleaned_data.get('fecha_hasta')
        tipo_nomina = filtro_form.cleaned_data.get('tipo_nomina')
        departamento = filtro_form.cleaned_data.get('departamento')
        
        if fecha_desde:
            nominas = nominas.filter(fecha_fin__gte=fecha_desde)
        
        if fecha_hasta:
            nominas = nominas.filter(fecha_inicio__lte=fecha_hasta)
            
        if tipo_nomina:
            nominas = nominas.filter(tipo_nomina=tipo_nomina)
            
        if departamento:
            nominas = nominas.filter(empleado__puesto__departamento=departamento)

    # Agregar filtro por estado (fuera del if del formulario)
    estado_filtro = request.GET.get('estado')
    if estado_filtro:
        nominas = nominas.filter(estado=estado_filtro)
    
    # Agrupar nóminas por fecha de generación y tipo
    nominas_agrupadas = {}
    for nomina in nominas:
        key = (nomina.fecha_generacion, nomina.tipo_nomina.id, nomina.estado)
        if key not in nominas_agrupadas:
            nominas_agrupadas[key] = {
                'fecha_generacion': nomina.fecha_generacion,
                'tipo_nomina': nomina.tipo_nomina,
                'fecha_inicio': nomina.fecha_inicio,
                'fecha_fin': nomina.fecha_fin,  
                'total_pagar': nomina.total_pagar,
                'estado': nomina.estado,
                'count': 1
            }
        else:
            nominas_agrupadas[key]['total_pagar'] += nomina.total_pagar
            nominas_agrupadas[key]['count'] += 1
    
    # Convertir a lista para paginación
    nominas_list = list(nominas_agrupadas.values())
    nominas_list.sort(key=lambda x: x['fecha_generacion'], reverse=True)
    
    # Paginación
    paginator = Paginator(nominas_list, 10)  # 10 nóminas por página
    page_number = request.GET.get('page', 1)
    nominas_pagina = paginator.get_page(page_number)
    
    context = {
        'nominas': nominas_pagina,
        'filtro_form': filtro_form,
    }
    
    return render(request, 'nomina_list.html', context)

@admin_required
def generar_nomina(request):
    """Vista para generar una nueva nómina"""
    if request.method == 'POST':
        form = GenerarNominaForm(request.POST)
        if form.is_valid():
            tipo_nomina = form.cleaned_data['tipo_nomina']
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']
            departamento = form.cleaned_data.get('departamento')
            
            # Obtener empleados activos
            empleados = Empleado.objects.filter(estado__nombre='Activo')
            if departamento:
                empleados = empleados.filter(puesto__departamento=departamento)
            
            if not empleados.exists():
                messages.error(request, "No hay empleados activos para generar la nómina.")
                return redirect('generar_nomina')
            
            # Crear formset inicial para cada empleado
            initial_data = [{'empleado_id': empleado.id} for empleado in empleados]
            formset = EmpleadoNominaFormSet(initial=initial_data)
            
            context = {
                'form': form,
                'formset': formset,
                'empleados': empleados,
                'tipo_nomina': tipo_nomina,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'departamento': departamento,
            }
            
            return render(request, 'nomina_empleados.html', context)
    else:
        # Por defecto, sugerir el período actual según el tipo de nómina
        hoy = timezone.now().date()
        inicio_mes = datetime.date(hoy.year, hoy.month, 1)
        fin_mes = datetime.date(hoy.year, hoy.month + 1, 1) - datetime.timedelta(days=1) if hoy.month < 12 else datetime.date(hoy.year + 1, 1, 1) - datetime.timedelta(days=1)
        
        form = GenerarNominaForm(initial={
            'fecha_inicio': inicio_mes,
            'fecha_fin': fin_mes,
        })
    
    context = {
        'form': form,
    }
    
    return render(request, 'generar_nomina.html', context)

@admin_required
@transaction.atomic
def procesar_nomina(request):
    """Vista para procesar y guardar la nómina"""
    if request.method == 'POST':
        tipo_nomina_id = request.POST.get('tipo_nomina')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        departamento_id = request.POST.get('departamento')

        tipo_nomina = get_object_or_404(TipoNomina, id=tipo_nomina_id)
        departamento = Departamento.objects.get(id=departamento_id) if departamento_id else None

        empleados = Empleado.objects.filter(estado__nombre='Activo')
        if departamento:
            empleados = empleados.filter(puesto__departamento=departamento)

        formset = EmpleadoNominaFormSet(request.POST)

        if formset.is_valid():
            fecha_generacion = timezone.now().date()
            nominas_creadas = []

            for form in formset:
                if form.is_valid():
                    empleado_id = form.cleaned_data['empleado_id']
                    empleado = get_object_or_404(Empleado, id=empleado_id)

                    horas_extras = form.cleaned_data.get('horas_extras') or 0
                    bonificaciones_adicionales = form.cleaned_data.get('bonificaciones_adicionales') or 0
                    deducciones_adicionales = form.cleaned_data.get('deducciones_adicionales') or 0
                    motivo_deduccion = form.cleaned_data.get('motivo_deduccion') or ''

                    # Llamar al SP para calcular la nómina
                    datos = calcular_nomina_sp(
                        empleado_id=empleado.id,
                        horas_extras=horas_extras,
                        bonificacion_adicional=bonificaciones_adicionales,
                        deduccion_adicional=deducciones_adicionales
                    )

                    if datos is None:
                        messages.error(request, f"No se pudo calcular la nómina para {empleado.nombre} {empleado.apellido}.")
                        continue

                    nomina = Nomina.objects.create(
                        empleado=empleado,
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                        tipo_nomina=tipo_nomina,
                        total_devengado=datos['total_devengado'],
                        total_deducciones=datos['total_deducciones'],
                        total_pagar=datos['total_pagar'],
                        fecha_generacion=fecha_generacion,
                        estado='Generada'
                    )

                    # Crear deducciones individuales
                    if datos['igss'] > 0:
                        Deduccion.objects.create(
                            nomina=nomina,
                            nombre="IGSS (4.83%)",
                            monto=datos['igss']
                        )
                    if datos['isr'] > 0:
                        Deduccion.objects.create(
                            nomina=nomina,
                            nombre="ISR (5%)",
                            monto=datos['isr']
                        )
                    if datos['otras_deducciones'] > 0:
                        Deduccion.objects.create(
                            nomina=nomina,
                            nombre=motivo_deduccion or "Deducción adicional",
                            monto=datos['otras_deducciones']
                        )

                    nominas_creadas.append(nomina)

            messages.success(request, f"Se han generado {len(nominas_creadas)} nóminas correctamente.")
            return redirect('nomina_list')
        else:
            messages.error(request, "Hay errores en el formulario. Por favor, corríjalos e intente nuevamente.")

    return redirect('generar_nomina')

@admin_required
def nomina_detalle(request, fecha_generacion, tipo_nomina_id):
    """Vista para ver el detalle de una nómina generada"""
    # Convertir fecha_generacion a objeto date
    fecha_generacion = datetime.datetime.strptime(fecha_generacion, "%Y-%m-%d").date()
    
    # Obtener tipo de nómina
    tipo_nomina = get_object_or_404(TipoNomina, id=tipo_nomina_id)
    
    # Obtener todas las nóminas de esa fecha y tipo
    nominas = Nomina.objects.filter(
        fecha_generacion=fecha_generacion,
        tipo_nomina=tipo_nomina
    ).select_related('empleado', 'empleado__puesto', 'empleado__puesto__departamento')
    
    if not nominas.exists():
        messages.error(request, "No se encontró la nómina solicitada.")
        return redirect('nomina_list')
    
    # Obtener primera nómina para datos generales
    primera_nomina = nominas.first()
    
    # Calcular totales
    total_devengado = nominas.aggregate(total=Sum('total_devengado'))['total'] or 0
    total_deducciones = nominas.aggregate(total=Sum('total_deducciones'))['total'] or 0
    total_pagar = nominas.aggregate(total=Sum('total_pagar'))['total'] or 0
    
    # Obtener deducciones agrupadas por tipo
    deducciones_igss = Deduccion.objects.filter(nomina__in=nominas, nombre__icontains='IGSS').aggregate(total=Sum('monto'))['total'] or 0
    deducciones_isr = Deduccion.objects.filter(nomina__in=nominas, nombre__icontains='ISR').aggregate(total=Sum('monto'))['total'] or 0
    deducciones_otras = Deduccion.objects.filter(nomina__in=nominas).exclude(nombre__icontains='IGSS').exclude(nombre__icontains='ISR').aggregate(total=Sum('monto'))['total'] or 0
    
    # Agrupar por departamento para estadísticas
    departamentos = {}
    for nomina in nominas:
        depto = nomina.empleado.puesto.departamento
        if depto.id not in departamentos:
            departamentos[depto.id] = {
                'nombre': depto.nombre,
                'empleados': 0,
                'total': 0
            }
        departamentos[depto.id]['empleados'] += 1
        departamentos[depto.id]['total'] += nomina.total_pagar
    
    context = {
        'nominas': nominas,
        'primera_nomina': primera_nomina,
        'fecha_generacion': fecha_generacion,
        'tipo_nomina': tipo_nomina,
        'total_devengado': total_devengado,
        'total_deducciones': total_deducciones,
        'total_pagar': total_pagar,
        'deducciones_igss': deducciones_igss,
        'deducciones_isr': deducciones_isr,
        'deducciones_otras': deducciones_otras,
        'departamentos': departamentos.values(),
        'isr_mensual': deducciones_isr,
    }
    
    return render(request, 'nomina_detalle.html', context)

@admin_or_empleado_required
def nomina_empleado(request, nomina_id):
    """Vista para ver boleta individual - Admin ve todas, Empleado solo las suyas"""
    nomina = get_object_or_404(Nomina, id=nomina_id)
    
    # Si es empleado, verificar que sea su nómina
    if request.user.rol.nombre == 'Empleado':
        if not request.user.empleado or nomina.empleado != request.user.empleado:
            messages.error(request, 'No tienes permisos para ver esta boleta de pago.')
            return redirect('dashboard')
    
    # Obtener las deducciones
    deducciones = Deduccion.objects.filter(nomina=nomina)
    
    # Calcular desglose del salario
    salario_base = nomina.empleado.puesto.salario_base
    
    # Ajustar salario base según tipo de nómina
    if nomina.tipo_nomina.nombre == 'Quincenal':
        salario_base = salario_base / decimal.Decimal('2')
    elif nomina.tipo_nomina.nombre == 'Semanal':
        salario_base = salario_base / decimal.Decimal('4.33')
    
    # Bonificación incentivo (ley de Guatemala: Q250.00 mensual)
    bonificacion_incentivo = decimal.Decimal('250.00')
    if nomina.tipo_nomina.nombre == 'Quincenal':
        bonificacion_incentivo = decimal.Decimal('250.00') / decimal.Decimal('2')
    elif nomina.tipo_nomina.nombre == 'Semanal':
        bonificacion_incentivo = decimal.Decimal('250.00') / decimal.Decimal('4.33')
    
    # Calcular otras bonificaciones
    total_sin_horas_extras = salario_base + bonificacion_incentivo
    horas_extras_valor = decimal.Decimal('0')
    
    if nomina.total_devengado > total_sin_horas_extras:
        diferencia = nomina.total_devengado - total_sin_horas_extras
        
        if nomina.tipo_nomina.nombre == 'Mensual':
            valor_hora = salario_base / decimal.Decimal('30') / decimal.Decimal('8')
        elif nomina.tipo_nomina.nombre == 'Quincenal':
            valor_hora = salario_base / decimal.Decimal('15') / decimal.Decimal('8')
        else:  # Semanal
            valor_hora = salario_base / decimal.Decimal('7') / decimal.Decimal('8')
        
        if diferencia > decimal.Decimal('0'):
            valor_hora_extra = valor_hora * decimal.Decimal('1.5')
            horas_extras = round(diferencia / valor_hora_extra, 2)
            horas_extras_valor = diferencia
        else:
            horas_extras = decimal.Decimal('0')
            horas_extras_valor = decimal.Decimal('0')
    else:
        horas_extras = decimal.Decimal('0')
        horas_extras_valor = decimal.Decimal('0')
    
    # Calcular deducciones
    igss = round(salario_base * decimal.Decimal('0.0483'), 2)
    isr_mensual = round(salario_base * decimal.Decimal('0.05'), 2)
    
    context = {
        'nomina': nomina,
        'deducciones': deducciones,
        'salario_base': salario_base,
        'bonificacion_incentivo': bonificacion_incentivo,
        'horas_extras': horas_extras,
        'horas_extras_valor': horas_extras_valor,
        'otras_bonificaciones': decimal.Decimal('0'),
        'igss': igss,
        'isr_mensual': isr_mensual,
        'is_admin': request.user.rol.nombre == 'Admin',
    }
    
    return render(request, 'nomina_empleado.html', context)

@admin_required
@transaction.atomic
def eliminar_nomina(request, fecha_generacion, tipo_nomina_id):
    """Vista para eliminar todas las nóminas de una fecha y tipo específicos"""
    if request.method == 'POST':
        # Convertir fecha_generacion a objeto date
        fecha_generacion = datetime.datetime.strptime(fecha_generacion, "%Y-%m-%d").date()
        
        # Obtener tipo de nómina
        tipo_nomina = get_object_or_404(TipoNomina, id=tipo_nomina_id)
        
        # Buscar todas las nóminas que coincidan con la fecha y tipo
        nominas = Nomina.objects.filter(
            fecha_generacion=fecha_generacion,
            tipo_nomina=tipo_nomina
        )
        
        if not nominas.exists():
            messages.error(request, "No se encontraron nóminas para eliminar.")
            return redirect('nomina_list')
        
        # Contar cuántas nóminas se eliminarán
        count = nominas.count()
        
        # Eliminar todas las deducciones asociadas y luego las nóminas
        for nomina in nominas:
            Deduccion.objects.filter(nomina=nomina).delete()
        
        nominas.delete()
        
        messages.success(request, f"Se han eliminado {count} nóminas correctamente.")
    
    return redirect('nomina_list')

@admin_required
def generar_reporte_nomina_pdf(request, fecha_generacion, tipo_nomina_id):
    """Vista para generar un reporte PDF de la nómina"""
    # Convertir fecha_generacion a objeto date
    fecha_generacion = datetime.datetime.strptime(fecha_generacion, "%Y-%m-%d").date()
    
    # Obtener tipo de nómina
    tipo_nomina = get_object_or_404(TipoNomina, id=tipo_nomina_id)
    
    # Obtener todas las nóminas de esa fecha y tipo
    nominas = Nomina.objects.filter(
        fecha_generacion=fecha_generacion,
        tipo_nomina=tipo_nomina
    ).select_related('empleado', 'empleado__puesto', 'empleado__puesto__departamento')
    
    if not nominas.exists():
        messages.error(request, "No se encontró la nómina solicitada.")
        return redirect('nomina_list')
    
    # Obtener fecha de inicio y fin (todas las nóminas tienen la misma)
    primera_nomina = nominas.first()
    fecha_inicio = primera_nomina.fecha_inicio
    fecha_fin = primera_nomina.fecha_fin
    
    # Generar el PDF
    pdf_buffer = generar_reporte_nomina(
        nominas, 
        tipo_nomina, 
        fecha_inicio, 
        fecha_fin, 
        fecha_generacion
    )
    
    # Crear la respuesta HTTP con el PDF
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="nomina_{tipo_nomina.nombre}_{fecha_generacion}.pdf"'
    
    return response

@admin_required
@transaction.atomic
def pagar_nomina(request, fecha_generacion, tipo_nomina_id):
    """Vista para marcar una nómina como pagada"""
    if request.method == 'POST':
        # Convertir fecha_generacion a objeto date
        fecha_generacion_obj = datetime.datetime.strptime(fecha_generacion, "%Y-%m-%d").date()
        tipo_nomina = get_object_or_404(TipoNomina, id=tipo_nomina_id)
        
        # Actualizar todas las nóminas de esa fecha y tipo
        nominas = Nomina.objects.filter(
            fecha_generacion=fecha_generacion_obj,
            tipo_nomina=tipo_nomina
        )
        
        if nominas.exists():
            nominas.update(estado='Pagada', fecha_pago=timezone.now().date())
            messages.success(request, "Nómina marcada como pagada exitosamente.")
        else:
            messages.error(request, "No se encontraron nóminas para actualizar.")
        
        return redirect('nomina_detalle', fecha_generacion=fecha_generacion, tipo_nomina_id=tipo_nomina_id)
    
    return redirect('nomina_list')

@admin_required
@transaction.atomic
def cancelar_nomina(request, fecha_generacion, tipo_nomina_id):
    """Vista para cancelar una nómina"""
    if request.method == 'POST':
        # Convertir fecha_generacion a objeto date
        fecha_generacion_obj = datetime.datetime.strptime(fecha_generacion, "%Y-%m-%d").date()
        tipo_nomina = get_object_or_404(TipoNomina, id=tipo_nomina_id)
        
        # Actualizar todas las nóminas de esa fecha y tipo
        nominas = Nomina.objects.filter(
            fecha_generacion=fecha_generacion_obj,
            tipo_nomina=tipo_nomina
        )
        
        if nominas.exists():
            nominas.update(estado='Cancelada')
            messages.success(request, "Nómina cancelada exitosamente.")
        else:
            messages.error(request, "No se encontraron nóminas para cancelar.")
        
        return redirect('nomina_detalle', fecha_generacion=fecha_generacion, tipo_nomina_id=tipo_nomina_id)
    
    return redirect('nomina_list')

def calcular_nomina_sp(empleado_id, horas_extras=0, bonificacion_adicional=0, deduccion_adicional=0):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT * FROM calcular_nomina(%s, %s, %s, %s);",
            [empleado_id, horas_extras, bonificacion_adicional, deduccion_adicional]
        )
        row = cursor.fetchone()

        if row:
            return {
                'salario_base': row[0],
                'bonificacion_incentivo': row[1],
                'horas_extras_valor': row[2],
                'total_devengado': row[3],
                'igss': row[4],
                'isr': row[5],
                'otras_deducciones': row[6],
                'total_deducciones': row[7],
                'total_pagar': row[8]
            }
    return None