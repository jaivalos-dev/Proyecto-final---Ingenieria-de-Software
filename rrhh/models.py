from django.db import models
from django.contrib.auth.models import AbstractUser

class Departamento(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Departamento")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"

class Puesto(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Puesto")
    salario_base = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Salario Base")
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name="puestos")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Puesto"
        verbose_name_plural = "Puestos"

class Estado(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Nombre del Estado")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"

class TipoNomina(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Tipo de Nómina")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Tipo de Nómina"
        verbose_name_plural = "Tipos de Nómina"

class TipoPrestacion(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Tipo de Prestación")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Tipo de Prestación"
        verbose_name_plural = "Tipos de Prestación"

class Empleado(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    dpi = models.CharField(max_length=20, unique=True, verbose_name="DPI")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento")
    fecha_ingreso = models.DateField(verbose_name="Fecha de Ingreso")
    fecha_baja = models.DateField(null=True, blank=True, verbose_name="Fecha de Baja")
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, related_name="empleados")
    direccion = models.CharField(max_length=255, verbose_name="Dirección")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    correo = models.EmailField(max_length=100, null=True, blank=True, verbose_name="Correo Electrónico")
    puesto = models.ForeignKey(Puesto, on_delete=models.CASCADE, related_name="empleados")
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

class Rol(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Nombre del Rol")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

class Usuario(AbstractUser):
    empleado = models.OneToOneField(Empleado, on_delete=models.SET_NULL, null=True, blank=True, related_name="usuario")
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name="usuarios", null=True)
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

class Nomina(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="nominas")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha Fin")
    tipo_nomina = models.ForeignKey(TipoNomina, on_delete=models.CASCADE, related_name="nominas")
    total_devengado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Devengado")
    total_deducciones = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Deducciones")
    total_pagar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total a Pagar")
    fecha_generacion = models.DateField(verbose_name="Fecha de Generación")
    
    def __str__(self):
        return f"Nómina de {self.empleado} ({self.fecha_inicio} a {self.fecha_fin})"
    
    class Meta:
        verbose_name = "Nómina"
        verbose_name_plural = "Nóminas"

class Deduccion(models.Model):
    nomina = models.ForeignKey(Nomina, on_delete=models.CASCADE, related_name="deducciones")
    nombre = models.CharField(max_length=100, verbose_name="Nombre de Deducción")
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    
    def __str__(self):
        return f"{self.nombre} - {self.monto}"
    
    class Meta:
        verbose_name = "Deducción"
        verbose_name_plural = "Deducciones"

class Prestacion(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="prestaciones")
    tipo_prestacion = models.ForeignKey(TipoPrestacion, on_delete=models.CASCADE, related_name="prestaciones")
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    fecha_prestacion = models.DateField(verbose_name="Fecha de Prestación")
    
    def __str__(self):
        return f"{self.tipo_prestacion} para {self.empleado}"
    
    class Meta:
        verbose_name = "Prestación"
        verbose_name_plural = "Prestaciones"

class IndicadorProductividad(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="indicadores")
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Indicador")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    fecha_registro = models.DateField(verbose_name="Fecha de Registro")
    
    def __str__(self):
        return f"{self.nombre} - {self.empleado}"
    
    class Meta:
        verbose_name = "Indicador de Productividad"
        verbose_name_plural = "Indicadores de Productividad"