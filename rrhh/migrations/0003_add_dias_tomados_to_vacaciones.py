# Generated by Django 5.2.1 on 2025-05-21 01:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rrhh', '0002_estadoprestacion_remove_prestacion_fecha_prestacion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacaciones',
            name='dias_tomados',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name='Días Tomados'),
        ),
    ]
