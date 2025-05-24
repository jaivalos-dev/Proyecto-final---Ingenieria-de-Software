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
    estado = models.CharField(max_length=20, choices=[
        ('Generada', 'Generada'),
        ('Pagada', 'Pagada'),
        ('Cancelada', 'Cancelada')
    ], default='Generada', verbose_name="Estado")
    fecha_pago = models.DateField(verbose_name="Fecha de Pago", null=True, blank=True)
    
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

class EstadoPrestacion(models.Model):
    """Estado de una prestación (Pendiente, Pagado, etc.)"""
    nombre = models.CharField(max_length=50, verbose_name="Nombre del Estado")
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Estado de Prestación"
        verbose_name_plural = "Estados de Prestación"

class Prestacion(models.Model):
    """Modelo para prestaciones (Aguinaldo y Bono 14)"""
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="prestaciones")
    tipo_prestacion = models.ForeignKey(TipoPrestacion, on_delete=models.CASCADE, related_name="prestaciones")
    monto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    fecha_calculo = models.DateField(verbose_name="Fecha de Cálculo", auto_now_add=True)
    fecha_pago = models.DateField(verbose_name="Fecha de Pago", null=True, blank=True)
    estado = models.ForeignKey(EstadoPrestacion, on_delete=models.CASCADE, related_name="prestaciones")
    periodo_inicio = models.DateField(verbose_name="Inicio del Período")
    periodo_fin = models.DateField(verbose_name="Fin del Período")
    observaciones = models.TextField(verbose_name="Observaciones", blank=True, null=True)
    
    def __str__(self):
        return f"{self.tipo_prestacion} para {self.empleado}"
    
    class Meta:
        verbose_name = "Prestación"
        verbose_name_plural = "Prestaciones"



class Vacaciones(models.Model):
    """Modelo para vacaciones"""
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name="vacaciones")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_fin = models.DateField(verbose_name="Fecha de Fin")
    dias_totales = models.PositiveIntegerField(verbose_name="Días Totales")
    dias_tomados = models.PositiveIntegerField(verbose_name="Días Tomados", default=0, null=True)  # Nuevo campo
    estado = models.CharField(max_length=50, choices=[
        ('Pendiente', 'Pendiente'),
        ('Aprobado', 'Aprobado'),
        ('Disfrutado', 'Disfrutado'),
        ('Pagado', 'Pagado')
    ], default='Pendiente', verbose_name="Estado")
    fecha_solicitud = models.DateField(verbose_name="Fecha de Solicitud", auto_now_add=True)
    fecha_aprobacion = models.DateField(verbose_name="Fecha de Aprobación", null=True, blank=True)
    aprobador = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="vacaciones_aprobadas")
    observaciones = models.TextField(verbose_name="Observaciones", blank=True, null=True)
    
    def __str__(self):
        return f"Vacaciones de {self.empleado} ({self.fecha_inicio} a {self.fecha_fin})"
    
    class Meta:
        verbose_name = "Vacaciones"
        verbose_name_plural = "Vacaciones"

class Liquidacion(models.Model):
    """Modelo simplificado para liquidaciones"""
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE, related_name="liquidacion")
    tipo = models.CharField(max_length=100, choices=[
        ('Renuncia', 'Renuncia'),
        ('Despido Justificado', 'Despido Justificado'),
        ('Despido Injustificado', 'Despido Injustificado')
    ], verbose_name="Tipo de Liquidación")
    estado = models.CharField(max_length=50, choices=[
        ('Pendiente', 'Pendiente'),
        ('Calculada', 'Calculada'),
        ('Pagada', 'Pagada')
    ], default='Pendiente', verbose_name="Estado")
    fecha_calculo = models.DateField(verbose_name="Fecha de Cálculo", auto_now_add=True)
    fecha_pago = models.DateField(verbose_name="Fecha de Pago", null=True, blank=True)
    
    # Montos
    indemnizacion = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Indemnización")
    vacaciones_pendientes = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Vacaciones Pendientes")
    aguinaldo_proporcional = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Aguinaldo Proporcional")
    bono14_proporcional = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Bono 14 Proporcional")
    
    # Totales
    total_ingresos = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Ingresos")
    total_deducciones = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Deducciones")
    total_liquidacion = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Liquidación")
    
    observaciones = models.TextField(verbose_name="Observaciones", blank=True, null=True)
    
    def __str__(self):
        return f"Liquidación de {self.empleado}"
    
    class Meta:
        verbose_name = "Liquidación"
        verbose_name_plural = "Liquidaciones"