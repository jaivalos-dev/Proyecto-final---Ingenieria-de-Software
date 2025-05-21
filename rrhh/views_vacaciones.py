# rrhh/views_vacaciones.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from .models import Empleado, Vacaciones

@login_required
def vacaciones_list(request):
    """Vista para mostrar vacaciones disponibles de todos los empleados"""
    
    # Obtener todos los empleados activos
    empleados = Empleado.objects.filter(estado__nombre='Activo').order_by('apellido')
    
    # Calcular vacaciones para cada empleado
    empleados_vacaciones = []
    for empleado in empleados:
        # Calcular tiempo de servicio
        hoy = timezone.now().date()
        años_servicio = relativedelta(hoy, empleado.fecha_ingreso).years
        
        # Calcular días de vacaciones según la ley guatemalteca
        # (15 días por año de servicio)
        dias_disponibles = años_servicio * 15
        
        # Obtener registro de vacaciones si existe, o crear uno nuevo
        vacaciones, created = Vacaciones.objects.get_or_create(
            empleado=empleado,
            defaults={
                'fecha_inicio': empleado.fecha_ingreso,
                'fecha_fin': hoy,
                'dias_totales': dias_disponibles,
                'estado': 'Pendiente',
                'observaciones': 'Generado automáticamente'
            }
        )
        
        if created:
            vacaciones.save()
        
        # Calcular días pendientes
        dias_pendientes = vacaciones.dias_totales - vacaciones.dias_tomados if hasattr(vacaciones, 'dias_tomados') else vacaciones.dias_totales
        
        empleados_vacaciones.append({
            'empleado': empleado,
            'años_servicio': años_servicio,
            'dias_disponibles': dias_disponibles,
            'dias_tomados': vacaciones.dias_tomados if hasattr(vacaciones, 'dias_tomados') else 0,
            'dias_pendientes': dias_pendientes,
            'vacaciones_id': vacaciones.id
        })
    
    context = {
        'empleados_vacaciones': empleados_vacaciones
    }
    
    return render(request, 'vacaciones_list.html', context)

@login_required
def actualizar_vacaciones(request, vacaciones_id):
    """Vista para actualizar los días tomados de vacaciones"""
    
    if request.method == 'POST':
        vacaciones = get_object_or_404(Vacaciones, id=vacaciones_id)
        dias_tomados = int(request.POST.get('dias_tomados', 0))
        
        # Validar que los días tomados no excedan los disponibles
        if dias_tomados <= vacaciones.dias_totales:
            vacaciones.dias_tomados = dias_tomados
            vacaciones.save()
            messages.success(request, "Días de vacaciones actualizados correctamente.")
        else:
            messages.error(request, "Los días tomados no pueden exceder los días disponibles.")
        
        return redirect('vacaciones_list')
    
    return redirect('vacaciones_list')