# Generated by Django 5.2.1 on 2025-05-21 00:37

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Departamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Nombre del Departamento')),
            ],
            options={
                'verbose_name': 'Departamento',
                'verbose_name_plural': 'Departamentos',
            },
        ),
        migrations.CreateModel(
            name='Estado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50, verbose_name='Nombre del Estado')),
            ],
            options={
                'verbose_name': 'Estado',
                'verbose_name_plural': 'Estados',
            },
        ),
        migrations.CreateModel(
            name='Rol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50, verbose_name='Nombre del Rol')),
            ],
            options={
                'verbose_name': 'Rol',
                'verbose_name_plural': 'Roles',
            },
        ),
        migrations.CreateModel(
            name='TipoNomina',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50, verbose_name='Tipo de Nómina')),
            ],
            options={
                'verbose_name': 'Tipo de Nómina',
                'verbose_name_plural': 'Tipos de Nómina',
            },
        ),
        migrations.CreateModel(
            name='TipoPrestacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50, verbose_name='Tipo de Prestación')),
            ],
            options={
                'verbose_name': 'Tipo de Prestación',
                'verbose_name_plural': 'Tipos de Prestación',
            },
        ),
        migrations.CreateModel(
            name='Empleado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Nombre')),
                ('apellido', models.CharField(max_length=100, verbose_name='Apellido')),
                ('dpi', models.CharField(max_length=20, unique=True, verbose_name='DPI')),
                ('fecha_nacimiento', models.DateField(verbose_name='Fecha de Nacimiento')),
                ('fecha_ingreso', models.DateField(verbose_name='Fecha de Ingreso')),
                ('fecha_baja', models.DateField(blank=True, null=True, verbose_name='Fecha de Baja')),
                ('direccion', models.CharField(max_length=255, verbose_name='Dirección')),
                ('telefono', models.CharField(max_length=20, verbose_name='Teléfono')),
                ('correo', models.EmailField(blank=True, max_length=100, null=True, verbose_name='Correo Electrónico')),
                ('estado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='empleados', to='rrhh.estado')),
            ],
            options={
                'verbose_name': 'Empleado',
                'verbose_name_plural': 'Empleados',
            },
        ),
        migrations.CreateModel(
            name='IndicadorProductividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Nombre del Indicador')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valor')),
                ('fecha_registro', models.DateField(verbose_name='Fecha de Registro')),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='indicadores', to='rrhh.empleado')),
            ],
            options={
                'verbose_name': 'Indicador de Productividad',
                'verbose_name_plural': 'Indicadores de Productividad',
            },
        ),
        migrations.CreateModel(
            name='Nomina',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_inicio', models.DateField(verbose_name='Fecha de Inicio')),
                ('fecha_fin', models.DateField(verbose_name='Fecha Fin')),
                ('total_devengado', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Total Devengado')),
                ('total_deducciones', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Total Deducciones')),
                ('total_pagar', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Total a Pagar')),
                ('fecha_generacion', models.DateField(verbose_name='Fecha de Generación')),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nominas', to='rrhh.empleado')),
                ('tipo_nomina', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nominas', to='rrhh.tiponomina')),
            ],
            options={
                'verbose_name': 'Nómina',
                'verbose_name_plural': 'Nóminas',
            },
        ),
        migrations.CreateModel(
            name='Deduccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Nombre de Deducción')),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto')),
                ('nomina', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deducciones', to='rrhh.nomina')),
            ],
            options={
                'verbose_name': 'Deducción',
                'verbose_name_plural': 'Deducciones',
            },
        ),
        migrations.CreateModel(
            name='Puesto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Nombre del Puesto')),
                ('salario_base', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Salario Base')),
                ('departamento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='puestos', to='rrhh.departamento')),
            ],
            options={
                'verbose_name': 'Puesto',
                'verbose_name_plural': 'Puestos',
            },
        ),
        migrations.AddField(
            model_name='empleado',
            name='puesto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='empleados', to='rrhh.puesto'),
        ),
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('empleado', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuario', to='rrhh.empleado')),
                ('rol', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='usuarios', to='rrhh.rol')),
            ],
            options={
                'verbose_name': 'Usuario',
                'verbose_name_plural': 'Usuarios',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Prestacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto')),
                ('fecha_prestacion', models.DateField(verbose_name='Fecha de Prestación')),
                ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prestaciones', to='rrhh.empleado')),
                ('tipo_prestacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prestaciones', to='rrhh.tipoprestacion')),
            ],
            options={
                'verbose_name': 'Prestación',
                'verbose_name_plural': 'Prestaciones',
            },
        ),
    ]
