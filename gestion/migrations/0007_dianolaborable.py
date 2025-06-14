# Generated by Django 5.2.1 on 2025-06-07 18:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0006_alter_diaatencion_dia_alter_turno_hora_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiaNoLaborable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('motivo', models.CharField(blank=True, max_length=100)),
                ('medico', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gestion.medico')),
            ],
        ),
    ]
