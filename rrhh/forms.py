from django import forms
from .models import Empleado, Puesto, Estado

# rrhh/forms.py - Mejorar el formulario de empleados

class EmpleadoForm(forms.ModelForm):
    """Formulario para crear y editar empleados"""
    
    # Campo oculto para el salario (solo informativo)
    salario_info = forms.DecimalField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
        label="Salario Base"
    )
    # Campo opcional para validar la contraseña si se desea crear un usuario asociado
    crear_usuario = forms.BooleanField(
        required=False, 
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Crear usuario del sistema"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label="Contraseña"
    )
    
    class Meta:
        model = Empleado
        fields = [
            'nombre', 'apellido', 'dpi', 'fecha_nacimiento', 'fecha_ingreso',
            'estado', 'direccion', 'telefono', 'correo', 'puesto'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'dpi': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'puesto': forms.Select(attrs={'class': 'form-select', 'id': 'id_puesto_select'}),
        }
    
    def clean_dpi(self):
        """Validar que el DPI sea único y cumpla con el formato guatemalteco"""
        dpi = self.cleaned_data.get('dpi')
        
        # Validar formato del DPI guatemalteco (13 dígitos)
        if len(dpi) != 13 or not dpi.isdigit():
            raise forms.ValidationError('El DPI debe tener 13 dígitos numéricos')
        
        # Verificar que no exista otro empleado con el mismo DPI
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # Si estamos editando un empleado existente
            if Empleado.objects.filter(dpi=dpi).exclude(pk=instance.pk).exists():
                raise forms.ValidationError('Ya existe un empleado con este DPI')
        else:
            # Si estamos creando un nuevo empleado
            if Empleado.objects.filter(dpi=dpi).exists():
                raise forms.ValidationError('Ya existe un empleado con este DPI')
        
        return dpi
    
    def clean(self):
        cleaned_data = super().clean()
        crear_usuario = cleaned_data.get('crear_usuario')
        password = cleaned_data.get('password')
        correo = cleaned_data.get('correo')
        
        if crear_usuario:
            if not password:
                self.add_error('password', 'Se requiere una contraseña para crear un usuario')
            if not correo:
                self.add_error('correo', 'Se requiere un correo electrónico para crear un usuario')
                
        return cleaned_data
    
    def save(self, commit=True):
        empleado = super().save(commit=commit)
        
        # Si se marcó la opción de crear usuario y se proporcionó una contraseña
        if commit and self.cleaned_data.get('crear_usuario') and self.cleaned_data.get('password'):
            # Comprobar si ya existe un usuario
            if not hasattr(empleado, 'usuario') or empleado.usuario is None:
                # Crear usuario
                username = f"{empleado.nombre.lower()}.{empleado.apellido.lower()}"
                username = username.replace(" ", "")
                
                # Verificar si ya existe el username y añadir un número si es necesario
                base_username = username
                count = 1
                while Usuario.objects.filter(username=username).exists():
                    username = f"{base_username}{count}"
                    count += 1
                
                # Obtener un rol por defecto
                try:
                    rol_empleado = Rol.objects.get(nombre="Empleado")
                except Rol.DoesNotExist:
                    # Si no existe, usar el primer rol disponible
                    rol_empleado = Rol.objects.first()
                
                usuario = Usuario.objects.create_user(
                    username=username,
                    email=empleado.correo,
                    password=self.cleaned_data.get('password'),
                    first_name=empleado.nombre,
                    last_name=empleado.apellido,
                    rol=rol_empleado
                )
                
                # Asociar el usuario al empleado
                empleado.usuario = usuario
                empleado.save()
        
        return empleado
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si estamos editando un empleado existente, mostrar el salario del puesto
        instance = kwargs.get('instance')
        if instance and instance.puesto:
            self.initial['salario_info'] = instance.puesto.salario_base