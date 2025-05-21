# rrhh/views_prestaciones.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.paginator import Paginator
import decimal
import datetime

from .models import Empleado, Prestacion, TipoPrestacion, EstadoPrestacion, Nomina

@login_required
def prestaciones_list(request):
    """Vista para listar todas las prestaciones"""
    # Filtrar prestaciones
    prestaciones = Prestacion.objects.all().order_by('-fecha_calculo')
    
    # Aplicar filtros si existen
    empleado_id = request.GET.get('empleado')
    tipo_id = request.GET.get('tipo')
    estado_id = request.GET.get('estado')
    
    if empleado_id:
        prestaciones = prestaciones.filter(empleado_id=empleado_id)
    
    if tipo_id:
        prestaciones = prestaciones.filter(tipo_prestacion_id=tipo_id)
    
    if estado_id:
        prestaciones = prestaciones.filter(estado_id=estado_id)
    
    # Paginación
    paginator = Paginator(prestaciones, 10)  # 10 prestaciones por página
    page_number = request.GET.get('page', 1)
    prestaciones_page = paginator.get_page(page_number)
    
    # Datos para los filtros
    empleados = Empleado.objects.filter(fecha_baja__isnull=True).order_by('apellido')
    tipos_prestacion = TipoPrestacion.objects.all()
    estados = EstadoPrestacion.objects.all()
    
    context = {
        'prestaciones': prestaciones_page,
        'empleados': empleados,
        'tipos_prestacion': tipos_prestacion,
        'estados': estados,
    }
    
    return render(request, 'prestaciones_list.html', context)

@login_required
def prestacion_detalle(request, pk):
    """Vista para ver detalle de una prestación"""
    prestacion = get_object_or_404(Prestacion, pk=pk)
    
    context = {
        'prestacion': prestacion,
    }
    
    return render(request, 'prestacion_detalle.html', context)

@login_required
def calcular_prestacion(request):
    """Vista para calcular una nueva prestación"""
    if request.method == 'POST':
        empleado_id = request.POST.get('empleado')
        tipo_prestacion_id = request.POST.get('tipo_prestacion')
        
        if not empleado_id or not tipo_prestacion_id:
            messages.error(request, "Por favor seleccione un empleado y un tipo de prestación.")
            return redirect('calcular_prestacion')
        
        empleado = get_object_or_404(Empleado, id=empleado_id)
        tipo_prestacion = get_object_or_404(TipoPrestacion, id=tipo_prestacion_id)
        
        try:
            # Definir período según tipo de prestación
            hoy = timezone.now().date()
            año_actual = hoy.year
            
            if tipo_prestacion.nombre == "Aguinaldo":
                # Aguinaldo: 1 de diciembre al 30 de noviembre
                if hoy.month < 12:  # Estamos antes de diciembre (ene-nov)
                    # Período anterior: 1 dic año-1 al 30 nov año actual
                    periodo_inicio = datetime.date(año_actual - 1, 12, 1)
                    periodo_fin = datetime.date(año_actual, 11, 30)
                else:  # Estamos en diciembre
                    # Período actual: 1 dic año actual al 30 nov año+1
                    periodo_inicio = datetime.date(año_actual, 12, 1)
                    periodo_fin = datetime.date(año_actual + 1, 11, 30)
            else:  # Bono 14
                # Bono 14: 1 de julio al 30 de junio
                if hoy.month < 7:  # Estamos antes de julio (ene-jun)
                    # Período anterior: 1 jul año-1 al 30 jun año actual
                    periodo_inicio = datetime.date(año_actual - 1, 7, 1)
                    periodo_fin = datetime.date(año_actual, 6, 30)
                else:  # Estamos en julio o después (jul-dic)
                    # Período actual: 1 jul año actual al 30 jun año+1
                    periodo_inicio = datetime.date(año_actual, 7, 1)
                    periodo_fin = datetime.date(año_actual + 1, 6, 30)
            
            # Si la fecha de fin es futura, usar hoy como fecha de fin para el cálculo
            fecha_fin_calculo = min(periodo_fin, hoy)
            
            # Para calcular el proporcional hasta hoy
            monto = calcular_monto_prestacion(empleado, tipo_prestacion, periodo_inicio, fecha_fin_calculo)
            
            # Verificar si ya existe una prestación para este empleado, tipo y período
            prestacion_existente = Prestacion.objects.filter(
                empleado=empleado,
                tipo_prestacion=tipo_prestacion,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin
            ).first()
            
            if prestacion_existente:
                messages.warning(request, f"Ya existe una prestación de {tipo_prestacion.nombre} para este período.")
                return redirect('prestacion_detalle', pk=prestacion_existente.id)
            
            # Obtener estado "Calculado"
            estado = EstadoPrestacion.objects.get(nombre="Calculado")
            
            # Crear la prestación (siempre con el período completo para referencia)
            prestacion = Prestacion.objects.create(
                empleado=empleado,
                tipo_prestacion=tipo_prestacion,
                monto=monto,
                estado=estado,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                observaciones=(
                    f"Calculado hasta {hoy.strftime('%d/%m/%Y')}.\n"
                    f"Días computados: {(fecha_fin_calculo - max(empleado.fecha_ingreso, periodo_inicio)).days + 1}.\n"
                    f"Salario base: Q{empleado.puesto.salario_base}.\n"
                    f"Proporcional al tiempo trabajado desde {max(empleado.fecha_ingreso, periodo_inicio).strftime('%d/%m/%Y')}."
                )
            )
            
            messages.success(request, (
                f"Prestación calculada exitosamente.\n"
                f"Monto: Q{monto:.2f}\n"
                f"Calculado desde {max(empleado.fecha_ingreso, periodo_inicio).strftime('%d/%m/%Y')} "
                f"hasta {fecha_fin_calculo.strftime('%d/%m/%Y')}"
            ))
            return redirect('prestacion_detalle', pk=prestacion.id)
            
        except Exception as e:
            messages.error(request, f"Error al calcular la prestación: {e}")
            return redirect('calcular_prestacion')
    
    # Si es GET, mostrar formulario
    empleados = Empleado.objects.filter(fecha_baja__isnull=True).order_by('apellido')
    tipos_prestacion = TipoPrestacion.objects.all()
    
    # Verificar si se pasó un empleado como parámetro
    empleado_id = request.GET.get('empleado')
    empleado_preseleccionado = None
    
    if empleado_id:
        try:
            empleado_preseleccionado = Empleado.objects.get(id=empleado_id)
        except Empleado.DoesNotExist:
            pass
    
    context = {
        'empleados': empleados,
        'tipos_prestacion': tipos_prestacion,
        'empleado_preseleccionado': empleado_preseleccionado,
    }
    
    return render(request, 'calcular_prestacion.html', context)

@login_required
@transaction.atomic
def pagar_prestacion(request, pk):
    """Vista para marcar una prestación como pagada"""
    prestacion = get_object_or_404(Prestacion, pk=pk)
    
    if request.method == 'POST':
        # Verificar que la prestación esté en estado Calculado
        if prestacion.estado.nombre != 'Calculado':
            messages.error(request, "Solo se pueden pagar prestaciones en estado 'Calculado'.")
            return redirect('prestacion_detalle', pk=pk)
        
        try:
            # Cambiar estado a Pagado
            estado_pagado = EstadoPrestacion.objects.get(nombre='Pagado')
            prestacion.estado = estado_pagado
            prestacion.fecha_pago = timezone.now().date()
            prestacion.save()
            
            messages.success(request, "Prestación marcada como pagada exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al marcar la prestación como pagada: {e}")
    
    return redirect('prestacion_detalle', pk=pk)

@login_required
@transaction.atomic
def cancelar_prestacion(request, pk):
    """Vista para cancelar una prestación"""
    prestacion = get_object_or_404(Prestacion, pk=pk)
    
    if request.method == 'POST':
        # Verificar que la prestación no esté en estado Pagado
        if prestacion.estado.nombre == 'Pagado':
            messages.error(request, "No se pueden cancelar prestaciones en estado 'Pagado'.")
            return redirect('prestacion_detalle', pk=pk)
        
        try:
            # Cambiar estado a Cancelado
            estado_cancelado = EstadoPrestacion.objects.get(nombre='Cancelado')
            prestacion.estado = estado_cancelado
            prestacion.save()
            
            messages.success(request, "Prestación cancelada exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al cancelar la prestación: {e}")
    
    return redirect('prestacion_detalle', pk=pk)

def calcular_monto_prestacion(empleado, tipo_prestacion, periodo_inicio, periodo_fin):
    """Calcular el monto de una prestación según el tipo y período"""
    # Calcular días totales del período completo (independientemente de fecha actual)
    # Para Aguinaldo: 1 dic al 30 nov = 365 días
    # Para Bono 14: 1 jul al 30 jun = 365 días
    if tipo_prestacion.nombre == "Aguinaldo":
        periodo_completo_inicio = datetime.date(periodo_inicio.year, 12, 1)
        periodo_completo_fin = datetime.date(periodo_inicio.year + 1, 11, 30)
    else:  # Bono 14
        periodo_completo_inicio = datetime.date(periodo_inicio.year, 7, 1)
        periodo_completo_fin = datetime.date(periodo_inicio.year + 1, 6, 30)
    
    dias_totales_completo = (periodo_completo_fin - periodo_completo_inicio).days + 1
    
    # Determinar días laborados en el período de cálculo
    # Desde la fecha de ingreso (o inicio del período, lo que sea posterior)
    fecha_inicio_calculo = max(empleado.fecha_ingreso, periodo_inicio)
    
    # Hasta la fecha de cálculo (o la fecha de baja, si existe y es anterior)
    fecha_fin_calculo = periodo_fin
    if empleado.fecha_baja and empleado.fecha_baja < periodo_fin:
        fecha_fin_calculo = empleado.fecha_baja
    
    # Días realmente laborados hasta la fecha de cálculo
    dias_laborados = (fecha_fin_calculo - fecha_inicio_calculo).days + 1
    dias_laborados = max(0, dias_laborados)  # Asegurar que no sea negativo
    
    # Factor proporcional según días laborados vs período completo
    factor_proporcion = decimal.Decimal(str(dias_laborados)) / decimal.Decimal(str(dias_totales_completo))
    
    # Obtener el salario base del empleado
    salario_base = empleado.puesto.salario_base
    
    # Logs para depuración (quitar en producción)
    print(f"Empleado: {empleado}")
    print(f"Tipo: {tipo_prestacion.nombre}")
    print(f"Período cálculo: {periodo_inicio} a {periodo_fin}")
    print(f"Período completo: {periodo_completo_inicio} a {periodo_completo_fin}")
    print(f"Fecha inicio cálculo: {fecha_inicio_calculo}")
    print(f"Fecha fin cálculo: {fecha_fin_calculo}")
    print(f"Días totales: {dias_totales_completo}")
    print(f"Días laborados: {dias_laborados}")
    print(f"Factor proporción: {factor_proporcion}")
    print(f"Salario base: {salario_base}")
    
    # Cálculo del monto según tipo de prestación
    monto = salario_base * factor_proporcion
    print(f"Monto calculado: {monto}")
    
    return monto

@login_required
@transaction.atomic
def recalcular_prestacion(request, pk):
    """Vista para recalcular una prestación existente"""
    prestacion = get_object_or_404(Prestacion, pk=pk)
    
    # Solo permitir recalcular prestaciones que no estén pagadas
    if prestacion.estado.nombre == 'Pagado':
        messages.error(request, "No se pueden recalcular prestaciones que ya han sido pagadas.")
        return redirect('prestacion_detalle', pk=pk)
    
    try:
        # Obtener datos necesarios
        empleado = prestacion.empleado
        tipo_prestacion = prestacion.tipo_prestacion
        periodo_inicio = prestacion.periodo_inicio
        periodo_fin = prestacion.periodo_fin
        hoy = timezone.now().date()
        
        # Usar la fecha actual como fecha de fin para el cálculo si el período termina en el futuro
        fecha_fin_calculo = min(periodo_fin, hoy)
        
        # Calcular el nuevo monto
        nuevo_monto = calcular_monto_prestacion(empleado, tipo_prestacion, periodo_inicio, fecha_fin_calculo)
        
        # Actualizar la prestación
        prestacion.monto = nuevo_monto
        prestacion.fecha_calculo = hoy
        prestacion.observaciones += f"\nRecalculado el {hoy.strftime('%d/%m/%Y')}. Monto anterior: Q{prestacion.monto:.2f}"
        prestacion.save()
        
        messages.success(request, f"Prestación recalculada exitosamente. Nuevo monto: Q{nuevo_monto:.2f}")
    except Exception as e:
        messages.error(request, f"Error al recalcular la prestación: {e}")
    
    return redirect('prestacion_detalle', pk=pk)

@login_required
@transaction.atomic
def eliminar_prestacion(request, pk):
    """Vista para eliminar una prestación"""
    prestacion = get_object_or_404(Prestacion, pk=pk)
    
    # Solo permitir eliminar prestaciones que no estén pagadas
    if prestacion.estado.nombre == 'Pagado':
        messages.error(request, "No se pueden eliminar prestaciones que ya han sido pagadas.")
        return redirect('prestacion_detalle', pk=pk)
    
    if request.method == 'POST':
        # Guardar información para el mensaje
        empleado_nombre = f"{prestacion.empleado.nombre} {prestacion.empleado.apellido}"
        tipo_prestacion = prestacion.tipo_prestacion.nombre
        
        # Eliminar la prestación
        prestacion.delete()
        
        messages.success(request, f"Prestación de {tipo_prestacion} para {empleado_nombre} eliminada exitosamente.")
        return redirect('prestaciones_list')
    
    return redirect('prestacion_detalle', pk=pk)