from django import forms
from .models import Empleado, Puesto, Estado

class EmpleadoForm(forms.ModelForm):
    """Formulario para crear y editar empleados"""
    
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
            'puesto': forms.Select(attrs={'class': 'form-select'}),
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