# rrhh/views_liquidaciones.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
from dateutil.relativedelta import relativedelta
import decimal
import datetime

from .models import Empleado, Liquidacion, Vacaciones, TipoPrestacion, Prestacion, EstadoPrestacion, Estado
from .decorators import admin_required, empleado_required, admin_or_empleado_required


@admin_required
def liquidaciones_list(request):
    """Vista para listar todas las liquidaciones"""
    liquidaciones = Liquidacion.objects.all().order_by('-fecha_calculo')
    
    # Aplicar filtros si existen
    empleado_id = request.GET.get('empleado')
    estado = request.GET.get('estado')
    
    if empleado_id:
        liquidaciones = liquidaciones.filter(empleado_id=empleado_id)
    
    if estado:
        liquidaciones = liquidaciones.filter(estado=estado)
    
    # Paginación
    paginator = Paginator(liquidaciones, 10)
    page_number = request.GET.get('page', 1)
    liquidaciones_page = paginator.get_page(page_number)
    
    # Datos para los filtros
    empleados = Empleado.objects.all().order_by('apellido')
    estados_liquidacion = [
        ('Pendiente', 'Pendiente'),
        ('Calculada', 'Calculada'),
        ('Pagada', 'Pagada')
    ]
    
    context = {
        'liquidaciones': liquidaciones_page,
        'empleados': empleados,
        'estados_liquidacion': estados_liquidacion,
    }
    
    return render(request, 'liquidaciones_list.html', context)

@admin_required
def liquidacion_detalle(request, pk):
    """Vista para ver detalle de una liquidación"""
    liquidacion = get_object_or_404(Liquidacion, pk=pk)
    
    context = {
        'liquidacion': liquidacion,
    }
    
    return render(request, 'liquidacion_detalle.html', context)

@admin_required
def calcular_liquidacion(request):
    """Vista para calcular una nueva liquidación"""
    if request.method == 'POST':
        empleado_id = request.POST.get('empleado')
        
        if not empleado_id:
            messages.error(request, "Por favor seleccione un empleado.")
            return redirect('calcular_liquidacion')
        
        empleado = get_object_or_404(Empleado, id=empleado_id)
        
        # Verificar que el empleado no tenga ya una liquidación
        if hasattr(empleado, 'liquidacion'):
            messages.error(request, "Este empleado ya tiene una liquidación generada.")
            return redirect('liquidacion_detalle', pk=empleado.liquidacion.id)
        
        try:
            with transaction.atomic():
                # Calcular la liquidación
                liquidacion_data = calcular_montos_liquidacion(empleado)
                
                # Crear la liquidación
                liquidacion = Liquidacion.objects.create(
                    empleado=empleado,
                    tipo='Liquidación General',
                    estado='Calculada',
                    indemnizacion=liquidacion_data['indemnizacion'],
                    vacaciones_pendientes=liquidacion_data['vacaciones_pendientes'],
                    aguinaldo_proporcional=liquidacion_data['aguinaldo_proporcional'],
                    bono14_proporcional=liquidacion_data['bono14_proporcional'],
                    total_ingresos=liquidacion_data['total_ingresos'],
                    total_deducciones=liquidacion_data['total_deducciones'],
                    total_liquidacion=liquidacion_data['total_liquidacion'],
                    observaciones=liquidacion_data['observaciones']
                )
                
                # Marcar al empleado como de baja
                empleado.fecha_baja = timezone.now().date()
                empleado.estado = Estado.objects.get(nombre='De baja')
                empleado.save()
                
                messages.success(request, f"Liquidación calculada exitosamente para {empleado.nombre} {empleado.apellido}.")
                return redirect('liquidacion_detalle', pk=liquidacion.id)
                
        except Exception as e:
            messages.error(request, f"Error al calcular la liquidación: {str(e)}")
            return redirect('calcular_liquidacion')
    
    # Si es GET, mostrar formulario
    empleados = Empleado.objects.filter(fecha_baja__isnull=True).order_by('apellido')
    
    context = {
        'empleados': empleados,
    }
    
    return render(request, 'calcular_liquidacion.html', context)

def calcular_montos_liquidacion(empleado):
    """Función para calcular todos los montos de liquidación"""
    hoy = timezone.now().date()
    salario_base = empleado.puesto.salario_base
    
    # 1. Calcular indemnización (1 mes de salario por año trabajado)
    años_servicio = relativedelta(hoy, empleado.fecha_ingreso).years
    meses_servicio = relativedelta(hoy, empleado.fecha_ingreso).months
    
    # Si tiene menos de un año, calcular proporcional
    if años_servicio == 0:
        indemnizacion = (salario_base / 12) * meses_servicio
    else:
        # Un mes completo por cada año, más proporcional de los meses adicionales
        indemnizacion = (años_servicio * salario_base) + ((salario_base / 12) * meses_servicio)
    
    # 2. Calcular vacaciones pendientes
    vacaciones_pendientes = calcular_vacaciones_pendientes(empleado, hoy)
    
    # 3. Calcular aguinaldo proporcional (1 dic - 30 nov)
    aguinaldo_proporcional = calcular_aguinaldo_proporcional(empleado, hoy)
    
    # 4. Calcular bono 14 proporcional (1 jul - 30 jun)
    bono14_proporcional = calcular_bono14_proporcional(empleado, hoy)
    
    # 5. Calcular salario proporcional del mes actual
    salario_proporcional = calcular_salario_proporcional(empleado, hoy)
    
    # 6. Totales
    total_ingresos = (indemnizacion + vacaciones_pendientes + 
                     aguinaldo_proporcional + bono14_proporcional + salario_proporcional)
    
    # Deducciones (IGSS sobre salario proporcional solamente)
    igss_deduccion = salario_proporcional * decimal.Decimal('0.0483')
    total_deducciones = igss_deduccion
    
    total_liquidacion = total_ingresos - total_deducciones
    
    # Observaciones
    observaciones = f"""
    Liquidación calculada el {hoy.strftime('%d/%m/%Y')}
    Tiempo de servicio: {años_servicio} años y {meses_servicio} meses
    Salario base: Q{salario_base}
    Salario proporcional del mes: Q{salario_proporcional:.2f}
    Deducción IGSS (4.83%): Q{igss_deduccion:.2f}
    """
    
    return {
        'indemnizacion': indemnizacion,
        'vacaciones_pendientes': vacaciones_pendientes,
        'aguinaldo_proporcional': aguinaldo_proporcional,
        'bono14_proporcional': bono14_proporcional,
        'salario_proporcional': salario_proporcional,
        'total_ingresos': total_ingresos,
        'total_deducciones': total_deducciones,
        'total_liquidacion': total_liquidacion,
        'observaciones': observaciones
    }

def calcular_vacaciones_pendientes(empleado, fecha_calculo):
    """Calcular vacaciones pendientes no gozadas"""
    años_servicio = relativedelta(fecha_calculo, empleado.fecha_ingreso).years
    dias_disponibles = años_servicio * 15  # 15 días por año según ley guatemalteca
    
    # Obtener días tomados del registro de vacaciones
    try:
        vacaciones = Vacaciones.objects.get(empleado=empleado)
        dias_tomados = vacaciones.dias_tomados if hasattr(vacaciones, 'dias_tomados') else 0
    except Vacaciones.DoesNotExist:
        dias_tomados = 0
    
    dias_pendientes = max(0, dias_disponibles - dias_tomados)
    
    # Convertir días a monto (dividir salario mensual entre 30 días)
    valor_dia = empleado.puesto.salario_base / 30
    monto_vacaciones = dias_pendientes * valor_dia
    
    return monto_vacaciones

def calcular_aguinaldo_proporcional(empleado, fecha_calculo):
    """Calcular aguinaldo proporcional hasta la fecha de liquidación"""
    # Período de aguinaldo: 1 diciembre al 30 noviembre
    año_actual = fecha_calculo.year
    
    if fecha_calculo.month < 12:
        # Estamos en el período que inició en diciembre del año anterior
        inicio_periodo = datetime.date(año_actual - 1, 12, 1)
        fin_periodo = datetime.date(año_actual, 11, 30)
    else:
        # Estamos en diciembre, período actual
        inicio_periodo = datetime.date(año_actual, 12, 1)
        fin_periodo = datetime.date(año_actual + 1, 11, 30)
    
    # Calcular días trabajados en el período hasta la fecha de liquidación
    fecha_inicio_calculo = max(empleado.fecha_ingreso, inicio_periodo)
    fecha_fin_calculo = min(fecha_calculo, fin_periodo)
    
    if fecha_fin_calculo < fecha_inicio_calculo:
        return decimal.Decimal('0')
    
    dias_trabajados = (fecha_fin_calculo - fecha_inicio_calculo).days + 1
    dias_totales_periodo = 365  # Un año completo
    
    factor_proporcional = decimal.Decimal(str(dias_trabajados)) / decimal.Decimal(str(dias_totales_periodo))
    aguinaldo_proporcional = empleado.puesto.salario_base * factor_proporcional
    
    return aguinaldo_proporcional

def calcular_bono14_proporcional(empleado, fecha_calculo):
    """Calcular bono 14 proporcional hasta la fecha de liquidación"""
    # Período de bono 14: 1 julio al 30 junio
    año_actual = fecha_calculo.year
    
    if fecha_calculo.month < 7:
        # Estamos en el período que inició en julio del año anterior
        inicio_periodo = datetime.date(año_actual - 1, 7, 1)
        fin_periodo = datetime.date(año_actual, 6, 30)
    else:
        # Estamos en julio o después, período actual
        inicio_periodo = datetime.date(año_actual, 7, 1)
        fin_periodo = datetime.date(año_actual + 1, 6, 30)
    
    # Calcular días trabajados en el período hasta la fecha de liquidación
    fecha_inicio_calculo = max(empleado.fecha_ingreso, inicio_periodo)
    fecha_fin_calculo = min(fecha_calculo, fin_periodo)
    
    if fecha_fin_calculo < fecha_inicio_calculo:
        return decimal.Decimal('0')
    
    dias_trabajados = (fecha_fin_calculo - fecha_inicio_calculo).days + 1
    dias_totales_periodo = 365  # Un año completo
    
    factor_proporcional = decimal.Decimal(str(dias_trabajados)) / decimal.Decimal(str(dias_totales_periodo))
    bono14_proporcional = empleado.puesto.salario_base * factor_proporcional
    
    return bono14_proporcional

def calcular_salario_proporcional(empleado, fecha_calculo):
    """Calcular salario proporcional del mes en curso"""
    # Obtener el primer día del mes actual
    primer_dia_mes = fecha_calculo.replace(day=1)
    
    # Calcular días trabajados en el mes hasta la fecha de liquidación
    dias_trabajados_mes = fecha_calculo.day
    
    # Días totales del mes
    if fecha_calculo.month == 12:
        siguiente_mes = fecha_calculo.replace(year=fecha_calculo.year + 1, month=1, day=1)
    else:
        siguiente_mes = fecha_calculo.replace(month=fecha_calculo.month + 1, day=1)
    
    ultimo_dia_mes = siguiente_mes - datetime.timedelta(days=1)
    dias_totales_mes = ultimo_dia_mes.day
    
    # Calcular salario proporcional
    factor_proporcional = decimal.Decimal(str(dias_trabajados_mes)) / decimal.Decimal(str(dias_totales_mes))
    salario_proporcional = empleado.puesto.salario_base * factor_proporcional
    
    return salario_proporcional

@admin_required
@transaction.atomic
def pagar_liquidacion(request, pk):
    """Vista para marcar una liquidación como pagada"""
    liquidacion = get_object_or_404(Liquidacion, pk=pk)
    
    if request.method == 'POST':
        if liquidacion.estado != 'Calculada':
            messages.error(request, "Solo se pueden pagar liquidaciones en estado 'Calculada'.")
        else:
            liquidacion.estado = 'Pagada'
            liquidacion.fecha_pago = timezone.now().date()
            liquidacion.save()
            messages.success(request, "Liquidación marcada como pagada exitosamente.")
        
        return redirect('liquidacion_detalle', pk=pk)
    
    return redirect('liquidacion_detalle', pk=pk)

@admin_required
@transaction.atomic
def eliminar_liquidacion(request, pk):
    """Vista para eliminar una liquidación"""
    liquidacion = get_object_or_404(Liquidacion, pk=pk)
    
    if liquidacion.estado == 'Pagada':
        messages.error(request, "No se pueden eliminar liquidaciones que ya han sido pagadas.")
        return redirect('liquidacion_detalle', pk=pk)
    
    if request.method == 'POST':
        empleado = liquidacion.empleado
        empleado_nombre = f"{empleado.nombre} {empleado.apellido}"
        
        # Reactivar al empleado si la liquidación se elimina
        empleado.fecha_baja = None
        try:
            estado_activo = Estado.objects.get(nombre='Activo')
            empleado.estado = estado_activo
        except:
            pass
        empleado.save()
        
        # Eliminar la liquidación
        liquidacion.delete()
        
        messages.success(request, f"Liquidación de {empleado_nombre} eliminada exitosamente. El empleado ha sido reactivado.")
        return redirect('liquidaciones_list')
    
    return redirect('liquidacion_detalle', pk=pk)