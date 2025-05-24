# rrhh/management/commands/generar_datos_historicos.py

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
    Empleado, Rol, Usuario, Nomina, Deduccion, Prestacion, 
    Vacaciones, Liquidacion, EstadoPrestacion
)

fake = Faker('es_ES')

class Command(BaseCommand):
    help = 'Genera datos históricos de 8 años para el sistema de RRHH'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empleados',
            type=int,
            default=50,
            help='Número de empleados a generar (default: 50)'
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando generación de datos históricos...\n')
        
        # Verificar si ya hay muchos datos
        num_empleados_existentes = Empleado.objects.count()
        if num_empleados_existentes > 10:
            respuesta = input(f"⚠️  Ya tienes {num_empleados_existentes} empleados en la base de datos. ¿Continuar? (y/N): ")
            if respuesta.lower() != 'y':
                self.stdout.write('❌ Operación cancelada por el usuario.')
                return
        
        with transaction.atomic():
            # 1. Crear datos maestros
            self.crear_datos_maestros()
            
            # 2. Generar empleados históricos
            num_empleados = options['empleados']
            empleados = self.generar_empleados_historicos(num_empleados)
            
            # 3. Generar nóminas históricas
            self.generar_nominas_historicas(empleados)
            
            # 4. Generar prestaciones históricas
            self.generar_prestaciones_historicas(empleados)
            
            # 5. Generar vacaciones históricas
            self.generar_vacaciones_historicas(empleados)
            
            # 6. Generar algunas liquidaciones históricas
            self.generar_liquidaciones_historicas(empleados)

        self.stdout.write(
            self.style.SUCCESS('✅ Datos históricos generados exitosamente!')
        )

    def crear_datos_maestros(self):
        """Crear o verificar datos maestros necesarios"""
        self.stdout.write('📋 Verificando y creando datos maestros...')
        
        # Verificar si ya hay datos
        if Departamento.objects.exists():
            self.stdout.write('⚠️  Ya existen departamentos. Saltando creación de datos maestros.')
            return
        
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
        
        # Roles
        roles_data = ['Administrador', 'Gerente', 'Supervisor', 'Empleado', 'Recursos Humanos']
        for rol_name in roles_data:
            rol, created = Rol.objects.get_or_create(nombre=rol_name)
            if created:
                self.stdout.write(f'✅ Rol creado: {rol_name}')
        
        # Crear puestos con salarios realistas para Guatemala
        self.crear_puestos_con_salarios()
        
        self.stdout.write('✅ Datos maestros verificados/creados')

    def crear_puestos_con_salarios(self):
        """Crear puestos con salarios realistas"""
        # Verificar si ya hay puestos
        if Puesto.objects.exists():
            self.stdout.write('⚠️  Ya existen puestos. Saltando creación de puestos.')
            return
            
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
                        self.stdout.write(f'✅ Puesto creado: {puesto_nombre} - Q{salario}')

    def generar_empleados_historicos(self, num_empleados):
        """Generar empleados con fechas de ingreso en los últimos 8 años"""
        self.stdout.write(f'👥 Generando {num_empleados} empleados históricos...')
        
        empleados = []
        puestos = list(Puesto.objects.all())
        estado_activo = Estado.objects.get(nombre='Activo')
        estado_baja = Estado.objects.get(nombre='De baja')
        
        # Fecha límite: 8 años atrás
        fecha_inicio = date.today() - relativedelta(years=8)
        fecha_fin = date.today() - relativedelta(months=1)  # Hasta el mes pasado
        
        for i in range(num_empleados):
            # Generar fecha de ingreso aleatoria en los últimos 8 años
            fecha_ingreso = fake.date_between(start_date=fecha_inicio, end_date=fecha_fin)
            
            # 90% empleados activos, 10% dados de baja
            if random.random() < 0.9:
                estado = estado_activo
                fecha_baja = None
            else:
                estado = estado_baja
                # Calcular fecha mínima de baja (6 meses después del ingreso)
                fecha_minima_baja = fecha_ingreso + relativedelta(months=6)
                
                # Solo asignar fecha de baja si la fecha mínima es antes de hoy
                if fecha_minima_baja <= date.today():
                    fecha_baja = fake.date_between(
                        start_date=fecha_minima_baja,
                        end_date=date.today()
                    )
                else:
                    # Si no se puede dar de baja (muy reciente), mantener activo
                    estado = estado_activo
                    fecha_baja = None
            
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
        
        self.stdout.write(f'✅ {len(empleados)} empleados generados')
        return empleados

    def generar_dpi_unico(self):
        """Generar un DPI único de 13 dígitos"""
        while True:
            dpi = ''.join([str(random.randint(0, 9)) for _ in range(13)])
            if not Empleado.objects.filter(dpi=dpi).exists():
                return dpi

    def generar_nominas_historicas(self, empleados):
        """Generar nóminas históricas para todos los empleados"""
        self.stdout.write('💰 Generando nóminas históricas...')
        
        tipos_nomina = list(TipoNomina.objects.all())
        
        for empleado in empleados:
            self.stdout.write(f'  📋 Generando nóminas para {empleado.nombre} {empleado.apellido}')
            
            # Determinar período de trabajo
            fecha_inicio_nominas = empleado.fecha_ingreso
            fecha_fin_nominas = empleado.fecha_baja if empleado.fecha_baja else date.today()
            
            # Generar nóminas mensuales principalmente
            fecha_actual = fecha_inicio_nominas.replace(day=1)  # Primer día del mes de ingreso
            
            while fecha_actual < fecha_fin_nominas:
                # 80% nóminas mensuales, 15% quincenales, 5% semanales
                rand = random.random()
                if rand < 0.8:
                    tipo_nomina = TipoNomina.objects.get(nombre='Mensual')
                    fecha_fin_periodo = self.ultimo_dia_mes(fecha_actual)
                elif rand < 0.95:
                    tipo_nomina = TipoNomina.objects.get(nombre='Quincenal')
                    if fecha_actual.day <= 15:
                        fecha_fin_periodo = fecha_actual.replace(day=15)
                    else:
                        fecha_fin_periodo = self.ultimo_dia_mes(fecha_actual)
                else:
                    tipo_nomina = TipoNomina.objects.get(nombre='Semanal')
                    fecha_fin_periodo = fecha_actual + timedelta(days=6)
                
                # No generar nóminas futuras
                if fecha_fin_periodo > fecha_fin_nominas:
                    fecha_fin_periodo = fecha_fin_nominas
                
                if fecha_actual <= fecha_fin_periodo:
                    self.crear_nomina_individual(empleado, fecha_actual, fecha_fin_periodo, tipo_nomina)
                
                # Avanzar al siguiente período
                if tipo_nomina.nombre == 'Mensual':
                    fecha_actual = fecha_actual + relativedelta(months=1)
                elif tipo_nomina.nombre == 'Quincenal':
                    if fecha_actual.day <= 15:
                        fecha_actual = fecha_actual.replace(day=16)
                    else:
                        fecha_actual = fecha_actual + relativedelta(months=1, day=1)
                else:  # Semanal
                    fecha_actual = fecha_actual + timedelta(days=7)
        
        self.stdout.write('✅ Nóminas históricas generadas')

    def ultimo_dia_mes(self, fecha):
        """Obtener el último día del mes"""
        siguiente_mes = fecha + relativedelta(months=1, day=1)
        return siguiente_mes - timedelta(days=1)

    def crear_nomina_individual(self, empleado, fecha_inicio, fecha_fin, tipo_nomina):
        """Crear una nómina individual con cálculos realistas"""
        
        # Verificar si ya existe la nómina
        if Nomina.objects.filter(
            empleado=empleado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo_nomina=tipo_nomina
        ).exists():
            return
        
        salario_base = empleado.puesto.salario_base
        
        # Ajustar salario según tipo de nómina
        if tipo_nomina.nombre == 'Quincenal':
            salario_periodo = salario_base / 2
            bonificacion_incentivo = decimal.Decimal('125.00')  # Q250/2
        elif tipo_nomina.nombre == 'Semanal':
            salario_periodo = salario_base / decimal.Decimal('4.33')
            bonificacion_incentivo = decimal.Decimal('57.74')  # Q250/4.33
        else:  # Mensual
            salario_periodo = salario_base
            bonificacion_incentivo = decimal.Decimal('250.00')
        
        # Generar horas extras ocasionalmente (30% de probabilidad)
        horas_extras = 0
        if random.random() < 0.3:
            horas_extras = random.randint(1, 15)
        
        # Calcular valor de hora extra
        valor_hora = salario_periodo / 30 / 8  # 30 días, 8 horas por día
        monto_horas_extras = valor_hora * decimal.Decimal('1.5') * horas_extras
        
        # Bonificaciones adicionales ocasionales (20% de probabilidad)
        bonificaciones_adicionales = decimal.Decimal('0')
        if random.random() < 0.2:
            bonificaciones_adicionales = decimal.Decimal(str(random.randint(200, 1000)))
        
        # Total devengado
        total_devengado = salario_periodo + bonificacion_incentivo + monto_horas_extras + bonificaciones_adicionales
        
        # Calcular deducciones
        igss = salario_periodo * decimal.Decimal('0.0483')
        isr = salario_periodo * decimal.Decimal('0.05') if salario_base > 5000 else decimal.Decimal('0')
        
        # Deducciones adicionales ocasionales (10% de probabilidad)
        deducciones_adicionales = decimal.Decimal('0')
        if random.random() < 0.1:
            deducciones_adicionales = decimal.Decimal(str(random.randint(50, 300)))
        
        total_deducciones = igss + isr + deducciones_adicionales
        total_pagar = total_devengado - total_deducciones
        
        # Crear la nómina
        nomina = Nomina.objects.create(
            empleado=empleado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo_nomina=tipo_nomina,
            total_devengado=total_devengado,
            total_deducciones=total_deducciones,
            total_pagar=total_pagar,
            fecha_generacion=fecha_fin + timedelta(days=random.randint(1, 5))
        )
        
        # Crear deducciones
        if igss > 0:
            Deduccion.objects.create(
                nomina=nomina,
                nombre="IGSS (4.83%)",
                monto=igss
            )
        
        if isr > 0:
            Deduccion.objects.create(
                nomina=nomina,
                nombre="ISR (5%)",
                monto=isr
            )
        
        if deducciones_adicionales > 0:
            Deduccion.objects.create(
                nomina=nomina,
                nombre="Deducción adicional",
                monto=deducciones_adicionales
            )

    def generar_prestaciones_historicas(self, empleados):
        """Generar prestaciones históricas (aguinaldos y bonos 14)"""
        self.stdout.write('🎁 Generando prestaciones históricas...')
        
        aguinaldo = TipoPrestacion.objects.get(nombre='Aguinaldo')
        bono14 = TipoPrestacion.objects.get(nombre='Bono 14')
        estado_pagado = EstadoPrestacion.objects.get(nombre='Pagado')
        estado_calculado = EstadoPrestacion.objects.get(nombre='Calculado')
        
        # Generar para los últimos 8 años
        año_actual = date.today().year
        
        for empleado in empleados:
            # Año de ingreso del empleado
            año_ingreso = empleado.fecha_ingreso.year
            
            for año in range(año_ingreso, año_actual + 1):
                # Aguinaldo (se paga en diciembre)
                if año > año_ingreso or empleado.fecha_ingreso.month <= 11:
                    # Solo si el empleado estuvo trabajando en el período del aguinaldo
                    fecha_calculo = date(año, 12, 15)
                    
                    # Verificar si el empleado seguía activo
                    if not empleado.fecha_baja or empleado.fecha_baja >= fecha_calculo:
                        monto_aguinaldo = self.calcular_monto_prestacion_historica(
                            empleado, año, 'aguinaldo'
                        )
                        
                        if monto_aguinaldo > 0:
                            Prestacion.objects.get_or_create(
                                empleado=empleado,
                                tipo_prestacion=aguinaldo,
                                periodo_inicio=date(año-1, 12, 1),
                                periodo_fin=date(año, 11, 30),
                                defaults={
                                    'monto': monto_aguinaldo,
                                    'estado': estado_pagado if año < año_actual else estado_calculado,
                                    'fecha_pago': fecha_calculo if año < año_actual else None,
                                    'observaciones': f'Aguinaldo {año} generado automáticamente'
                                }
                            )
                
                # Bono 14 (se paga en julio)
                if año > año_ingreso or empleado.fecha_ingreso.month <= 6:
                    fecha_calculo = date(año, 7, 15)
                    
                    # Verificar si el empleado seguía activo
                    if not empleado.fecha_baja or empleado.fecha_baja >= fecha_calculo:
                        monto_bono14 = self.calcular_monto_prestacion_historica(
                            empleado, año, 'bono14'
                        )
                        
                        if monto_bono14 > 0:
                            Prestacion.objects.get_or_create(
                                empleado=empleado,
                                tipo_prestacion=bono14,
                                periodo_inicio=date(año-1, 7, 1),
                                periodo_fin=date(año, 6, 30),
                                defaults={
                                    'monto': monto_bono14,
                                    'estado': estado_pagado if año < año_actual else estado_calculado,
                                    'fecha_pago': fecha_calculo if año < año_actual else None,
                                    'observaciones': f'Bono 14 {año} generado automáticamente'
                                }
                            )
        
        self.stdout.write('✅ Prestaciones históricas generadas')

    def calcular_monto_prestacion_historica(self, empleado, año, tipo):
        """Calcular monto de prestación histórica"""
        salario_base = empleado.puesto.salario_base
        
        if tipo == 'aguinaldo':
            # Período: 1 dic año-1 al 30 nov año
            inicio_periodo = date(año-1, 12, 1)
            fin_periodo = date(año, 11, 30)
        else:  # bono14
            # Período: 1 jul año-1 al 30 jun año
            inicio_periodo = date(año-1, 7, 1)
            fin_periodo = date(año, 6, 30)
        
        # Calcular días trabajados en el período
        fecha_inicio_real = max(empleado.fecha_ingreso, inicio_periodo)
        fecha_fin_real = min(empleado.fecha_baja or date.today(), fin_periodo)
        
        if fecha_fin_real < fecha_inicio_real:
            return decimal.Decimal('0')
        
        dias_trabajados = (fecha_fin_real - fecha_inicio_real).days + 1
        dias_totales = (fin_periodo - inicio_periodo).days + 1
        
        factor_proporcional = decimal.Decimal(str(dias_trabajados)) / decimal.Decimal(str(dias_totales))
        return salario_base * factor_proporcional

    def generar_vacaciones_historicas(self, empleados):
        """Generar registros de vacaciones históricas"""
        self.stdout.write('🏖️ Generando vacaciones históricas...')
        
        for empleado in empleados:
            # Calcular años de servicio
            fecha_fin = empleado.fecha_baja if empleado.fecha_baja else date.today()
            años_servicio = relativedelta(fecha_fin, empleado.fecha_ingreso).years
            
            if años_servicio > 0:
                # 15 días por año según ley guatemalteca
                dias_disponibles = años_servicio * 15
                
                # Simular que tomaron entre 40% y 90% de sus vacaciones
                porcentaje_tomado = random.uniform(0.4, 0.9)
                dias_tomados = int(dias_disponibles * porcentaje_tomado)
                
                Vacaciones.objects.get_or_create(
                    empleado=empleado,
                    defaults={
                        'fecha_inicio': empleado.fecha_ingreso,
                        'fecha_fin': fecha_fin,
                        'dias_totales': dias_disponibles,
                        'dias_tomados': dias_tomados,
                        'estado': 'Disfrutado',
                        'observaciones': 'Registro histórico generado automáticamente'
                    }
                )
        
        self.stdout.write('✅ Vacaciones históricas generadas')

    def generar_liquidaciones_historicas(self, empleados):
        """Generar algunas liquidaciones históricas"""
        self.stdout.write('📄 Generando liquidaciones históricas...')
        
        # Solo para empleados dados de baja
        empleados_baja = [e for e in empleados if e.fecha_baja]
        
        # Generar liquidaciones para 70% de los empleados dados de baja
        empleados_liquidacion = random.sample(
            empleados_baja, 
            int(len(empleados_baja) * 0.7)
        )
        
        for empleado in empleados_liquidacion:
            if not hasattr(empleado, 'liquidacion'):
                # Calcular montos de liquidación
                salario_base = empleado.puesto.salario_base
                años_servicio = relativedelta(empleado.fecha_baja, empleado.fecha_ingreso).years
                
                # Indemnización: 1 mes por año
                indemnizacion = salario_base * años_servicio
                
                # Valores simulados para otros conceptos
                vacaciones_pendientes = decimal.Decimal(str(random.uniform(500, 3000)))
                aguinaldo_proporcional = decimal.Decimal(str(random.uniform(1000, 5000)))
                bono14_proporcional = decimal.Decimal(str(random.uniform(1000, 5000)))
                
                total_ingresos = (indemnizacion + vacaciones_pendientes + 
                                aguinaldo_proporcional + bono14_proporcional)
                total_deducciones = total_ingresos * decimal.Decimal('0.05')  # 5% deducciones
                total_liquidacion = total_ingresos - total_deducciones
                
                Liquidacion.objects.create(
                    empleado=empleado,
                    tipo='Liquidación General',
                    estado='Pagada',
                    fecha_pago=empleado.fecha_baja + timedelta(days=random.randint(1, 30)),
                    indemnizacion=indemnizacion,
                    vacaciones_pendientes=vacaciones_pendientes,
                    aguinaldo_proporcional=aguinaldo_proporcional,
                    bono14_proporcional=bono14_proporcional,
                    total_ingresos=total_ingresos,
                    total_deducciones=total_deducciones,
                    total_liquidacion=total_liquidacion,
                    observaciones='Liquidación histórica generada automáticamente'
                )
        
        self.stdout.write('✅ Liquidaciones históricas generadas')

# Si quieres ejecutar el script directamente
if __name__ == '__main__':
    command = Command()
    command.handle(empleados=50)