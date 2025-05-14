from django.contrib import admin
from .models import *

# Registrar todos los modelos
admin.site.register(Departamento)
admin.site.register(Puesto)
admin.site.register(Estado)
admin.site.register(TipoNomina)
admin.site.register(TipoPrestacion)
admin.site.register(Empleado)
admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(Nomina)
admin.site.register(Deduccion)
admin.site.register(Prestacion)
admin.site.register(IndicadorProductividad)