# Generated by Django 5.2.1 on 2025-05-22 02:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rrhh', '0003_add_dias_tomados_to_vacaciones'),
    ]

    operations = [
        migrations.DeleteModel(
            name='IndicadorProductividad',
        ),
    ]
