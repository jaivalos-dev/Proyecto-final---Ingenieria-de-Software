# Generated by Django 5.2.1 on 2025-05-22 03:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rrhh', '0004_remove_indicador_productividad'),
    ]

    operations = [
        migrations.AddField(
            model_name='nomina',
            name='estado',
            field=models.CharField(choices=[('Generada', 'Generada'), ('Pagada', 'Pagada'), ('Cancelada', 'Cancelada')], default='Generada', max_length=20, verbose_name='Estado'),
        ),
        migrations.AddField(
            model_name='nomina',
            name='fecha_pago',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha de Pago'),
        ),
    ]
