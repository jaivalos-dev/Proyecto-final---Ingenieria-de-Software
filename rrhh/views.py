from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from .models import Empleado, Departamento, Nomina, IndicadorProductividad, Rol, Usuario, Estado
from .forms import EmpleadoForm
from django.utils import timezone
import datetime

def dashboard(request):
    """Vista para el dashboard principal del sistema"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Obtener datos para el dashboard
    total_empleados = Empleado.objects.filter(fecha_baja__isnull=True).count()
    total_departamentos = Departamento.objects.count()
    
    # Intentar obtener el total de la nómina actual, si existe
    hoy = timezone.now().date()
    nomina_actual = Nomina.objects.filter(
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy
    ).aggregate(total=Sum('total_pagar'))
    total_nomina = nomina_actual['total'] if nomina_actual['total'] else 0
    
    # Calcular promedio de productividad (ejemplo)
    indicadores = IndicadorProductividad.objects.filter(
        fecha_registro__gte=hoy - datetime.timedelta(days=30)
    )
    productividad = 0
    if indicadores.exists():
        productividad = round(indicadores.aggregate(avg_valor=Sum('valor') / indicadores.count())['avg_valor'], 2)
    
    # Obtener empleados recientes
    empleados_recientes = Empleado.objects.filter(
        fecha_baja__isnull=True
    ).order_by('-fecha_ingreso')[:5]
    
    # Obtener próximas nóminas
    proximas_nominas = Nomina.objects.filter(
        fecha_fin__gte=hoy
    ).order_by('fecha_fin')[:5]
    
    context = {
        'total_empleados': total_empleados,
        'total_departamentos': total_departamentos,
        'total_nomina': total_nomina,
        'productividad': productividad,
        'empleados_recientes': empleados_recientes,
        'proximas_nominas': proximas_nominas,
    }
    
    return render(request, 'dashboard.html', context)

def login_view(request):
    """Vista para el inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.first_name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'login.html')

def register(request):
    """Vista para el registro de usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    roles = Rol.objects.all()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        rol_id = request.POST.get('rol')
        
        # Validaciones básicas
        if password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'register.html', {'roles': roles})
        
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya está en uso')
            return render(request, 'register.html', {'roles': roles})
        
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'El correo electrónico ya está en uso')
            return render(request, 'register.html', {'roles': roles})
        
        # Crear usuario
        try:
            rol = Rol.objects.get(id=rol_id)
            user = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                rol=rol
            )
            
            messages.success(request, 'Usuario registrado exitosamente. Ahora puedes iniciar sesión.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error al registrar el usuario: {str(e)}')
    
    return render(request, 'register.html', {'roles': roles})


@login_required
def empleados_list(request):
    """Vista para listar empleados con filtros y paginación"""
    
    # Obtener todos los empleados
    empleados = Empleado.objects.all().order_by('apellido')
    
    # Filtros
    nombre_filter = request.GET.get('nombre', '')
    departamento_filter = request.GET.get('departamento', '')
    estado_filter = request.GET.get('estado', '')
    
    if nombre_filter:
        empleados = empleados.filter(
            Q(nombre__icontains=nombre_filter) | Q(apellido__icontains=nombre_filter)
        )
    
    if departamento_filter:
        empleados = empleados.filter(puesto__departamento_id=departamento_filter)
    
    if estado_filter:
        empleados = empleados.filter(estado_id=estado_filter)
    
    # Paginación
    paginator = Paginator(empleados, 12)  # 12 empleados por página
    page_number = request.GET.get('page', 1)
    empleados_page = paginator.get_page(page_number)
    
    # Datos para los filtros
    departamentos = Departamento.objects.all().order_by('nombre')
    estados = Estado.objects.all().order_by('nombre')
    
    context = {
        'empleados': empleados_page,
        'departamentos': departamentos,
        'estados': estados,
    }
    
    return render(request, 'empleados_list.html', context)


@login_required
def empleado_nuevo(request):
    """Vista para crear un nuevo empleado"""
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado creado exitosamente.')
            return redirect('empleados_list')
    else:
        form = EmpleadoForm()
    
    return render(request, 'empleado_form.html', {
        'form': form,
        'titulo': 'Nuevo Empleado',
        'boton': 'Crear Empleado',
        'accion': 'crear'
    })


@login_required
def empleado_editar(request, pk):
    """Vista para editar un empleado existente"""
    empleado = get_object_or_404(Empleado, pk=pk)
    
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado actualizado exitosamente.')
            return redirect('empleados_list')
    else:
        form = EmpleadoForm(instance=empleado)
    
    return render(request, 'empleado_form.html', {
        'form': form,
        'empleado': empleado,
        'titulo': 'Editar Empleado',
        'boton': 'Actualizar Empleado',
        'accion': 'editar'
    })


@login_required
def empleado_detalle(request, pk):
    """Vista para ver los detalles de un empleado"""
    empleado = get_object_or_404(Empleado, pk=pk)
    return render(request, 'empleado_detalle.html', {'empleado': empleado})


@login_required
def empleado_eliminar(request, pk):
    """Vista para eliminar un empleado"""
    empleado = get_object_or_404(Empleado, pk=pk)
    
    if request.method == 'POST':
        # En lugar de eliminar, marcamos como inactivo o de baja
        estado_baja = Estado.objects.get(nombre='De baja')
        empleado.estado = estado_baja
        empleado.fecha_baja = timezone.now().date()
        empleado.save()
        
        messages.success(request, f'El empleado {empleado.nombre} {empleado.apellido} ha sido dado de baja.')
        return redirect('empleados_list')
    
    return redirect('empleados_list')