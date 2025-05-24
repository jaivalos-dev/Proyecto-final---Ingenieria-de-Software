# rrhh/management/commands/generar_datos_basicos.py

import os
import django
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import random
import decimal
from faker import Faker

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestor_rrhh.settings')
django.setup()

from rrhh.models import (
    Departamento, Puesto, Estado, TipoNomina, TipoPrestacion, 
    Empleado, Rol, Usuario, EstadoPrestacion, Vacaciones
)

fake = Faker('es_ES')

class Command(BaseCommand):
    help = 'Genera datos básicos del sistema (departamentos, puestos, empleados, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empleados',
            type=int,
            default=20,
            help='Número de empleados a generar (default: 20)'
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando generación de datos básicos del sistema...\n')
        
        with transaction.atomic():
            # 1. Crear datos maestros
            self.crear_datos_maestros()
            
            # 2. Generar empleados
            num_empleados = options['empleados']
            empleados = self.generar_empleados(num_empleados)
            
            # 3. Generar registros básicos de vacaciones
            self.generar_vacaciones_basicas(empleados)
            
            # 4. Crear usuarios de prueba
            self.crear_usuarios_prueba()

        self.stdout.write(
            self.style.SUCCESS('✅ Datos básicos del sistema generados exitosamente!')
        )

    def crear_datos_maestros(self):
        """Crear todos los datos maestros necesarios"""
        self.stdout.write('📋 Creando datos maestros...')
        
        # Departamentos
        departamentos_data = [
            'Recursos Humanos', 'Contabilidad', 'Ventas', 'Marketing',
            'Tecnología', 'Operaciones', 'Logística', 'Administración',
            'Producción', 'Calidad', 'Compras', 'Legal'
        ]
        
        for dept_name in departamentos_data:
            dept, created = Departamento.objects.get_or_create(nombre=dept_name)
            if created:
                self.stdout.write(f'✅ Departamento creado: {dept_name}')
        
        # Estados
        estados_data = ['Activo', 'Inactivo', 'De baja', 'Suspendido']
        for estado_name in estados_data:
            estado, created = Estado.objects.get_or_create(nombre=estado_name)
            if created:
                self.stdout.write(f'✅ Estado creado: {estado_name}')
        
        # Tipos de Nómina
        tipos_nomina = ['Mensual', 'Quincenal', 'Semanal']
        for tipo in tipos_nomina:
            tipo_obj, created = TipoNomina.objects.get_or_create(nombre=tipo)
            if created:
                self.stdout.write(f'✅ Tipo de nómina creado: {tipo}')
        
        # Tipos de Prestación
        tipos_prestacion = ['Aguinaldo', 'Bono 14']
        for tipo in tipos_prestacion:
            tipo_obj, created = TipoPrestacion.objects.get_or_create(nombre=tipo)
            if created:
                self.stdout.write(f'✅ Tipo de prestación creado: {tipo}')
        
        # Estados de Prestación
        estados_prestacion = ['Pendiente', 'Calculado', 'Pagado', 'Cancelado']
        for estado in estados_prestacion:
            estado_obj, created = EstadoPrestacion.objects.get_or_create(nombre=estado)
            if created:
                self.stdout.write(f'✅ Estado de prestación creado: {estado}')
        
        # Roles (solo Admin y Empleado)
        roles_data = ['Admin', 'Empleado']
        for rol_name in roles_data:
            rol, created = Rol.objects.get_or_create(nombre=rol_name)
            if created:
                self.stdout.write(f'✅ Rol creado: {rol_name}')
        
        # Crear puestos con salarios
        self.crear_puestos_con_salarios()
        
        self.stdout.write('✅ Datos maestros creados')

    def crear_puestos_con_salarios(self):
        """Crear puestos con salarios realistas para Guatemala"""
        self.stdout.write('💼 Creando puestos de trabajo...')
        
        departamentos = Departamento.objects.all()
        
        puestos_por_departamento = {
            'Recursos Humanos': [
                ('Gerente de RRHH', 15000),
                ('Analista de RRHH', 8000),
                ('Asistente de RRHH', 5000),
                ('Reclutador', 6000),
            ],
            'Contabilidad': [
                ('Contador General', 12000),
                ('Asistente Contable', 5500),
                ('Auxiliar Contable', 4000),
                ('Auditor Interno', 10000),
            ],
            'Ventas': [
                ('Gerente de Ventas', 14000),
                ('Ejecutivo de Ventas', 7000),
                ('Vendedor', 4500),
                ('Supervisor de Ventas', 9000),
            ],
            'Marketing': [
                ('Gerente de Marketing', 13000),
                ('Analista de Marketing', 7500),
                ('Diseñador Gráfico', 6000),
                ('Community Manager', 5000),
            ],
            'Tecnología': [
                ('Gerente de TI', 18000),
                ('Desarrollador Senior', 12000),
                ('Desarrollador Junior', 7000),
                ('Analista de Sistemas', 9000),
                ('Soporte Técnico', 5000),
            ],
            'Operaciones': [
                ('Gerente de Operaciones', 16000),
                ('Supervisor de Operaciones', 8000),
                ('Operario', 3500),
                ('Técnico', 5500),
            ],
            'Logística': [
                ('Gerente de Logística', 12000),
                ('Coordinador de Logística', 7000),
                ('Almacenista', 4000),
                ('Chofer', 4500),
            ],
            'Administración': [
                ('Gerente General', 25000),
                ('Asistente Administrativo', 4500),
                ('Recepcionista', 3500),
                ('Secretaria', 4000),
            ],
            'Producción': [
                ('Gerente de Producción', 15000),
                ('Supervisor de Producción', 8500),
                ('Operario de Producción', 3800),
                ('Técnico de Mantenimiento', 6000),
            ],
            'Calidad': [
                ('Gerente de Calidad', 13000),
                ('Inspector de Calidad', 6000),
                ('Analista de Calidad', 7500),
            ],
            'Compras': [
                ('Gerente de Compras', 12000),
                ('Analista de Compras', 7000),
                ('Asistente de Compras', 5000),
            ],
            'Legal': [
                ('Abogado Senior', 15000),
                ('Asistente Legal', 6000),
            ]
        }
        
        for dept in departamentos:
            if dept.nombre in puestos_por_departamento:
                for puesto_nombre, salario in puestos_por_departamento[dept.nombre]:
                    puesto, created = Puesto.objects.get_or_create(
                        nombre=puesto_nombre,
                        departamento=dept,
                        defaults={'salario_base': decimal.Decimal(str(salario))}
                    )
                    if created:
                        self.stdout.write(f'  ✅ Puesto creado: {puesto_nombre} - Q{salario}')
        
        self.stdout.write('✅ Puestos de trabajo creados')

    def generar_empleados(self, num_empleados):
        """Generar empleados básicos"""
        self.stdout.write(f'👥 Generando {num_empleados} empleados...')
        
        empleados = []
        puestos = list(Puesto.objects.all())
        estado_activo = Estado.objects.get(nombre='Activo')
        estado_baja = Estado.objects.get(nombre='De baja')
        
        # Fechas de ingreso en los últimos 5 años
        fecha_inicio = date.today() - relativedelta(years=5)
        fecha_fin = date.today() - relativedelta(months=1)
        
        for i in range(num_empleados):
            # 95% empleados activos, 5% dados de baja
            if random.random() < 0.95:
                estado = estado_activo
                fecha_baja = None
            else:
                estado = estado_baja
                # Fecha de baja aleatoria
                fecha_ingreso_temp = fake.date_between(start_date=fecha_inicio, end_date=fecha_fin)
                fecha_minima_baja = fecha_ingreso_temp + relativedelta(months=3)
                
                if fecha_minima_baja <= date.today():
                    fecha_baja = fake.date_between(
                        start_date=fecha_minima_baja,
                        end_date=date.today()
                    )
                else:
                    estado = estado_activo
                    fecha_baja = None
            
            # Generar fecha de ingreso
            fecha_ingreso = fake.date_between(start_date=fecha_inicio, end_date=fecha_fin)
            
            # Generar DPI único
            dpi = self.generar_dpi_unico()
            
            empleado = Empleado.objects.create(
                nombre=fake.first_name(),
                apellido=fake.last_name(),
                dpi=dpi,
                fecha_nacimiento=fake.date_of_birth(minimum_age=18, maximum_age=65),
                fecha_ingreso=fecha_ingreso,
                fecha_baja=fecha_baja,
                estado=estado,
                direccion=fake.address(),
                telefono=fake.phone_number()[:20],
                correo=fake.email(),
                puesto=random.choice(puestos)
            )
            empleados.append(empleado)
            
            # Mostrar progreso cada 5 empleados
            if (i + 1) % 5 == 0:
                self.stdout.write(f'  📝 {i + 1}/{num_empleados} empleados creados...')
        
        self.stdout.write(f'✅ {len(empleados)} empleados generados')
        return empleados

    def generar_dpi_unico(self):
        """Generar un DPI único de 13 dígitos"""
        while True:
            dpi = ''.join([str(random.randint(0, 9)) for _ in range(13)])
            if not Empleado.objects.filter(dpi=dpi).exists():
                return dpi

    def generar_vacaciones_basicas(self, empleados):
        """Generar registros básicos de vacaciones para cada empleado"""
        self.stdout.write('🏖️ Generando registros básicos de vacaciones...')
        
        for empleado in empleados:
            # Calcular años de servicio
            fecha_fin = empleado.fecha_baja if empleado.fecha_baja else date.today()
            años_servicio = relativedelta(fecha_fin, empleado.fecha_ingreso).years
            
            if años_servicio > 0:
                # 15 días por año según ley guatemalteca
                dias_disponibles = años_servicio * 15
                
                # Simular que han tomado entre 0% y 50% de sus vacaciones
                porcentaje_tomado = random.uniform(0.0, 0.5)
                dias_tomados = int(dias_disponibles * porcentaje_tomado)
                
                Vacaciones.objects.get_or_create(
                    empleado=empleado,
                    defaults={
                        'fecha_inicio': empleado.fecha_ingreso,
                        'fecha_fin': fecha_fin,
                        'dias_totales': dias_disponibles,
                        'dias_tomados': dias_tomados,
                        'estado': 'Pendiente',
                        'observaciones': 'Registro inicial generado automáticamente'
                    }
                )
        
        self.stdout.write('✅ Registros de vacaciones creados')

    def crear_usuarios_prueba(self):
        """Crear algunos usuarios de prueba para diferentes roles"""
        self.stdout.write('👤 Creando usuarios de prueba...')
        
        # Buscar empleados para asignar usuarios
        empleados_sin_usuario = Empleado.objects.filter(
            estado__nombre='Activo',
            usuario__isnull=True
        )[:4]  # Solo los primeros 4 (2 admin, 2 empleados)
        
        roles = {
            'Admin': 'admin123',
            'Empleado': 'empleado123'
        }
        
        for i, empleado in enumerate(empleados_sin_usuario):
            # Crear 2 usuarios Admin y 2 usuarios Empleado
            if i < 2:
                rol_nombre = 'Admin'
                password = 'admin123'
            else:
                rol_nombre = 'Empleado'
                password = 'empleado123'
            
            try:
                rol = Rol.objects.get(nombre=rol_nombre)
                
                # Crear username único
                username = f"{empleado.nombre.lower()}.{empleado.apellido.lower()}".replace(' ', '')
                base_username = username
                count = 1
                while Usuario.objects.filter(username=username).exists():
                    username = f"{base_username}{count}"
                    count += 1
                
                usuario = Usuario.objects.create_user(
                    username=username,
                    email=empleado.correo,
                    password=password,
                    first_name=empleado.nombre,
                    last_name=empleado.apellido,
                    rol=rol
                )
                
                # Asociar el usuario al empleado
                empleado.usuario = usuario
                empleado.save()
                
                self.stdout.write(f'  ✅ Usuario creado: {username} (Rol: {rol_nombre}, Password: {password})')
            
            except Exception as e:
                self.stdout.write(f'  ❌ Error creando usuario para {empleado.nombre}: {e}')
        
        self.stdout.write('✅ Usuarios de prueba creados')
        self.stdout.write('\n📝 Credenciales de acceso:')
        self.stdout.write('  🔑 Admin: username = [nombre.apellido] / password = admin123')
        self.stdout.write('  👤 Empleado: username = [nombre.apellido] / password = empleado123')
        self.stdout.write('\n🔐 Permisos:')
        self.stdout.write('  🛡️  Admin: Acceso completo al sistema')
        self.stdout.write('  👤 Empleado: Solo puede ver sus vacaciones y boletas de pago')

# Si quieres ejecutar el script directamente
if __name__ == '__main__':
    command = Command()
    command.handle(empleados=20)