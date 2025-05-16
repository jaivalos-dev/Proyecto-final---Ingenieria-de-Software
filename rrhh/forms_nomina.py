from django import forms
from django.forms import formset_factory
from django.utils import timezone
from .models import Empleado, TipoNomina, Nomina, Puesto, Departamento

class GenerarNominaForm(forms.Form):
    """Formulario para generar una nómina"""
    tipo_nomina = forms.ModelChoiceField(
        queryset=TipoNomina.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Tipo de Nómina"
    )
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Fecha de Inicio"
    )
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Fecha de Fin"
    )
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label="Departamento (Opcional)"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        
        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                raise forms.ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")
            
            # Verificar que no exista otra nómina en el mismo período para los mismos empleados
            tipo_nomina = cleaned_data.get("tipo_nomina")
            departamento = cleaned_data.get("departamento")
            
            query = Nomina.objects.filter(
                fecha_inicio__lte=fecha_fin,
                fecha_fin__gte=fecha_inicio,
                tipo_nomina=tipo_nomina
            )
            
            if departamento:
                query = query.filter(empleado__puesto__departamento=departamento)
                
            if query.exists():
                raise forms.ValidationError(
                    "Ya existe una nómina para el período y tipo seleccionado. Por favor, verifique las fechas."
                )
        
        return cleaned_data

class EmpleadoNominaForm(forms.Form):
    """Formulario para ingresar datos específicos de nómina por empleado"""
    empleado_id = forms.IntegerField(widget=forms.HiddenInput())
    horas_extras = forms.DecimalField(
        max_digits=5, 
        decimal_places=2,
        min_value=0,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Horas Extras"
    )
    bonificaciones_adicionales = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=0,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Bonificaciones Adicionales"
    )
    deducciones_adicionales = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        min_value=0,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Deducciones Adicionales"
    )
    motivo_deduccion = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Motivo de Deducción"
    )

# Formset para manejar múltiples empleados en una sola nómina
EmpleadoNominaFormSet = formset_factory(EmpleadoNominaForm, extra=0)

class FiltroNominaForm(forms.Form):
    """Formulario para filtrar nóminas generadas"""
    fecha_desde = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False,
        label="Fecha Desde"
    )
    fecha_hasta = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False,
        label="Fecha Hasta"
    )
    tipo_nomina = forms.ModelChoiceField(
        queryset=TipoNomina.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label="Tipo de Nómina"
    )
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label="Departamento"
    )