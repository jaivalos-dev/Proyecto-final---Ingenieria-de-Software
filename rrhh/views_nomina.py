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

from .models import Empleado, Nomina, Deduccion, TipoNomina, Departamento, Estado, Puesto
from .forms_nomina import GenerarNominaForm, EmpleadoNominaFormSet, FiltroNominaForm

@login_required
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
    
    # Agrupar nóminas por fecha de generación y tipo
    nominas_agrupadas = {}
    for nomina in nominas:
        key = (nomina.fecha_generacion, nomina.tipo_nomina.id)
        if key not in nominas_agrupadas:
            nominas_agrupadas[key] = {
                'fecha_generacion': nomina.fecha_generacion,
                'tipo_nomina': nomina.tipo_nomina,
                'fecha_inicio': nomina.fecha_inicio,
                'fecha_fin': nomina.fecha_fin,
                'total_pagar': nomina.total_pagar,
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

@login_required
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

@login_required
@transaction.atomic
def procesar_nomina(request):
    """Vista para procesar y guardar la nómina"""
    if request.method == 'POST':
        # Recuperar parámetros
        tipo_nomina_id = request.POST.get('tipo_nomina')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        departamento_id = request.POST.get('departamento')
        
        tipo_nomina = get_object_or_404(TipoNomina, id=tipo_nomina_id)
        departamento = Departamento.objects.get(id=departamento_id) if departamento_id else None
        
        # Obtener empleados activos
        empleados = Empleado.objects.filter(estado__nombre='Activo')
        if departamento:
            empleados = empleados.filter(puesto__departamento=departamento)
        
        # Procesar formset
        formset = EmpleadoNominaFormSet(request.POST)
        
        if formset.is_valid():
            fecha_generacion = timezone.now().date()
            nominas_creadas = []
            
            for form in formset:
                if form.is_valid():
                    # Obtener datos del empleado
                    empleado_id = form.cleaned_data['empleado_id']
                    empleado = get_object_or_404(Empleado, id=empleado_id)
                    
                    # Obtener datos adicionales
                    horas_extras = form.cleaned_data.get('horas_extras') or 0
                    bonificaciones_adicionales = form.cleaned_data.get('bonificaciones_adicionales') or 0
                    deducciones_adicionales = form.cleaned_data.get('deducciones_adicionales') or 0
                    motivo_deduccion = form.cleaned_data.get('motivo_deduccion') or ''
                    
                    # Calcular la nómina según el tipo (usar funciones de PostgreSQL)
                    salario_base = empleado.puesto.salario_base
                    bonificacion_incentivo = decimal.Decimal('250.00')  # Por ley en Guatemala
                    
                    # Calcular el valor de horas extras (1.5 veces el valor normal)
                    valor_hora = salario_base / 30 / 8  # Salario diario / 8 horas
                    monto_horas_extras = valor_hora * decimal.Decimal('1.5') * horas_extras
                    
                    # Total devengado
                    total_devengado = salario_base + bonificacion_incentivo + monto_horas_extras + bonificaciones_adicionales
                    
                    # Calcular deducciones
                    # IGSS (4.83% sobre el salario base y horas extras, no sobre bonificaciones)
                    base_igss = salario_base + monto_horas_extras
                    igss = round(base_igss * decimal.Decimal('0.0483'), 2)
                    
                    # ISR (depende del salario anual)
                    salario_anual = salario_base * 12
                    isr_mensual = 0
                    
                    if salario_anual > 300000:
                        # 5% sobre el excedente de Q300,000
                        isr_anual = (salario_anual - 300000) * decimal.Decimal('0.05')
                        isr_mensual = round(isr_anual / 12, 2)
                    
                    # Total deducciones
                    total_deducciones = igss + isr_mensual + deducciones_adicionales
                    
                    # Total a pagar
                    total_pagar = total_devengado - total_deducciones
                    
                    # Crear la nómina
                    nomina = Nomina.objects.create(
                        empleado=empleado,
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                        tipo_nomina=tipo_nomina,
                        total_devengado=total_devengado,
                        total_deducciones=total_deducciones,
                        total_pagar=total_pagar,
                        fecha_generacion=fecha_generacion
                    )
                    
                    # Crear deducciones
                    if igss > 0:
                        Deduccion.objects.create(
                            nomina=nomina,
                            nombre="IGSS",
                            monto=igss
                        )
                    
                    if isr_mensual > 0:
                        Deduccion.objects.create(
                            nomina=nomina,
                            nombre="ISR",
                            monto=isr_mensual
                        )
                    
                    if deducciones_adicionales > 0:
                        Deduccion.objects.create(
                            nomina=nomina,
                            nombre=motivo_deduccion or "Deducción adicional",
                            monto=deducciones_adicionales
                        )
                    
                    nominas_creadas.append(nomina)
            
            messages.success(request, f"Se han generado {len(nominas_creadas)} nóminas correctamente.")
            return redirect('nomina_list')
        else:
            messages.error(request, "Hay errores en el formulario. Por favor, corríjalos e intente nuevamente.")
    
    # Si hay error o es GET, redirigir a generar nómina
    return redirect('generar_nomina')

@login_required
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
    
    context = {
        'nominas': nominas,
        'primera_nomina': primera_nomina,
        'fecha_generacion': fecha_generacion,
        'tipo_nomina': tipo_nomina,
        'total_devengado': total_devengado,
        'total_deducciones': total_deducciones,
        'total_pagar': total_pagar,
    }
    
    return render(request, 'nomina_detalle.html', context)

@login_required
def nomina_empleado(request, nomina_id):
    """Vista para ver el detalle de una nómina de un empleado específico"""
    nomina = get_object_or_404(Nomina, id=nomina_id)
    deducciones = Deduccion.objects.filter(nomina=nomina)
    
    # Calcular desglose del salario
    salario_base = nomina.empleado.puesto.salario_base
    bonificacion_incentivo = decimal.Decimal('250.00')  # Fijo por ley
    
    # Calcular horas extras (si existen)
    horas_extras_valor = nomina.total_devengado - salario_base - bonificacion_incentivo
    horas_extras = 0
    
    if horas_extras_valor > 0:
        valor_hora = salario_base / 30 / 8
        horas_extras = round(horas_extras_valor / (valor_hora * decimal.Decimal('1.5')), 2)
    
    context = {
        'nomina': nomina,
        'deducciones': deducciones,
        'salario_base': salario_base,
        'bonificacion_incentivo': bonificacion_incentivo,
        'horas_extras': horas_extras,
        'horas_extras_valor': horas_extras_valor,
    }
    
    return render(request, 'nomina_empleado.html', context)