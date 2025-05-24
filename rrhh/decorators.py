# rrhh/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def admin_required(view_func):
    """Decorador que requiere que el usuario sea Admin"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not hasattr(request.user, 'rol') or request.user.rol.nombre != 'Admin':
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def empleado_required(view_func):
    """Decorador que requiere que el usuario sea Empleado"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not hasattr(request.user, 'rol') or request.user.rol.nombre != 'Empleado':
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_or_empleado_required(view_func):
    """Decorador que permite tanto Admin como Empleado"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not hasattr(request.user, 'rol') or request.user.rol.nombre not in ['Admin', 'Empleado']:
            messages.error(request, 'No tienes permisos para acceder a esta sección.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper