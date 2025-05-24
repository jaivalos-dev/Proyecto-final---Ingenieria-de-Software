# rrhh/views_vacaciones.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from .models import Empleado, Vacaciones
from .decorators import admin_required, empleado_required, admin_or_empleado_required

@admin_or_empleado_required
def vacaciones_list(request):
    """Vista para listar vacaciones - Admin ve todas, Empleado solo las suyas"""
    
    # Si es Admin, ve todas las vacaciones
    if request.user.rol.nombre == 'Admin':
        vacaciones = Vacaciones.objects.all().order_by('-fecha_solicitud')
        empleados = Empleado.objects.filter(fecha_baja__isnull=True).order_by('apellido')
        
        # Aplicar filtros si existen
        empleado_id = request.GET.get('empleado')
        estado = request.GET.get('estado')
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        if empleado_id:
            vacaciones = vacaciones.filter(empleado_id=empleado_id)
        
        if estado:
            vacaciones = vacaciones.filter(estado=estado)
        
        if fecha_desde:
            vacaciones = vacaciones.filter(fecha_fin__gte=fecha_desde)
        
        if fecha_hasta:
            vacaciones = vacaciones.filter(fecha_inicio__lte=fecha_hasta)
        
        # Calcular vacaciones para cada empleado
        empleados_vacaciones = []
        for empleado in empleados:
            # Calcular tiempo de servicio
            hoy = timezone.now().date()
            años_servicio = relativedelta(hoy, empleado.fecha_ingreso).years
            
            # Calcular días de vacaciones según la ley guatemalteca
            dias_disponibles = años_servicio * 15
            
            # Obtener registro de vacaciones si existe
            try:
                vacaciones_emp = Vacaciones.objects.get(empleado=empleado)
                dias_tomados = vacaciones_emp.dias_tomados
            except Vacaciones.DoesNotExist:
                dias_tomados = 0
            
            dias_pendientes = dias_disponibles - dias_tomados
            
            empleados_vacaciones.append({
                'empleado': empleado,
                'años_servicio': años_servicio,
                'dias_disponibles': dias_disponibles,
                'dias_tomados': dias_tomados,
                'dias_pendientes': dias_pendientes,
                'vacaciones_id': vacaciones_emp.id if 'vacaciones_emp' in locals() else None
            })
        
        context = {
            'empleados_vacaciones': empleados_vacaciones,
            'is_admin': True
        }
        
        return render(request, 'vacaciones_list.html', context)
    
    # Si es Empleado, solo ve sus vacaciones
    else:
        empleado = request.user.empleado
        if not empleado:
            messages.error(request, 'Tu usuario no tiene un empleado asociado.')
            return redirect('dashboard')
        
        # Calcular tiempo de servicio
        hoy = timezone.now().date()
        años_servicio = relativedelta(hoy, empleado.fecha_ingreso).years
        dias_disponibles = años_servicio * 15
        
        # Obtener registro de vacaciones
        try:
            vacaciones_emp = Vacaciones.objects.get(empleado=empleado)
            dias_tomados = vacaciones_emp.dias_tomados
            vacaciones_id = vacaciones_emp.id
        except Vacaciones.DoesNotExist:
            dias_tomados = 0
            vacaciones_id = None
        
        dias_pendientes = dias_disponibles - dias_tomados
        
        empleados_vacaciones = [{
            'empleado': empleado,
            'años_servicio': años_servicio,
            'dias_disponibles': dias_disponibles,
            'dias_tomados': dias_tomados,
            'dias_pendientes': dias_pendientes,
            'vacaciones_id': vacaciones_id
        }]
        
        context = {
            'empleados_vacaciones': empleados_vacaciones,
            'is_admin': False
        }
        
        return render(request, 'vacaciones_empleado.html', context)

@admin_required  # Solo admin puede actualizar días tomados
def actualizar_vacaciones(request, vacaciones_id):
    """Vista para actualizar los días tomados de vacaciones - Solo Admin"""
    
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