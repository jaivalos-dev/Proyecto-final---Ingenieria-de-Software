from django.core.management.base import BaseCommand
from rrhh.models import Rol, Estado, TipoNomina, TipoPrestacion, Departamento

class Command(BaseCommand):
    help = 'Crea datos iniciales necesarios para el sistema'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creando datos iniciales...')
        
        # Crear roles
        roles = [
            'Administrador',
            'Recursos Humanos',
            'Gerente',
            'Empleado'
        ]
        
        for rol_nombre in roles:
            Rol.objects.get_or_create(nombre=rol_nombre)
        
        self.stdout.write(self.style.SUCCESS(f'Roles creados: {len(roles)}'))
        
        # Crear estados
        estados = [
            'Activo',
            'Inactivo',
            'De baja',
            'Suspendido'
        ]
        
        for estado_nombre in estados:
            Estado.objects.get_or_create(nombre=estado_nombre)
        
        self.stdout.write(self.style.SUCCESS(f'Estados creados: {len(estados)}'))
        
        # Crear tipos de nómina
        tipos_nomina = [
            'Mensual',
            'Quincenal',
            'Semanal'
        ]
        
        for tipo_nombre in tipos_nomina:
            TipoNomina.objects.get_or_create(nombre=tipo_nombre)
        
        self.stdout.write(self.style.SUCCESS(f'Tipos de nómina creados: {len(tipos_nomina)}'))
        
        # Crear tipos de prestación
        tipos_prestacion = [
            'Aguinaldo',
            'Bono 14',
            'Vacaciones',
            'Indemnización',
            'Bonificación Incentivo'
        ]
        
        for tipo_nombre in tipos_prestacion:
            TipoPrestacion.objects.get_or_create(nombre=tipo_nombre)
        
        self.stdout.write(self.style.SUCCESS(f'Tipos de prestación creados: {len(tipos_prestacion)}'))
        
        # Crear departamentos básicos
        departamentos = [
            'Recursos Humanos',
            'Administración',
            'Finanzas',
            'Tecnología',
            'Operaciones',
            'Ventas',
            'Marketing'
        ]
        
        for depto_nombre in departamentos:
            Departamento.objects.get_or_create(nombre=depto_nombre)
        
        self.stdout.write(self.style.SUCCESS(f'Departamentos creados: {len(departamentos)}'))
        
        self.stdout.write(self.style.SUCCESS('Datos iniciales creados correctamente'))