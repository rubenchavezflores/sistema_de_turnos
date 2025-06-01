from django.db import models
from django.utils import timezone
from datetime import datetime

class Especialidad(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Medico(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

DIAS_SEMANA = [
    ('LUNES', 'Lunes'),
    ('MARTES', 'Martes'),
    ('MIERCOLES', 'Miércoles'),
    ('JUEVES', 'Jueves'),
    ('VIERNES', 'Viernes'),
    ('SABADO', 'Sábado'),
    ('DOMINGO', 'Domingo'),
]

class DiaAtencion(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='dias_atencion')
    dia = models.CharField(max_length=10)  # ej. "LUNES"
    horario_inicio = models.TimeField()
    horario_fin = models.TimeField()
    intervalo_minutos = models.IntegerField()

    def __str__(self):
        return f"{self.dia} - {self.horario_inicio} a {self.horario_fin} cada {self.intervalo_minutos} min"


class Paciente(models.Model):
    dni = models.CharField(max_length=15, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.dni})"

class Turno(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()

    def __str__(self):
        return f"Turno con {self.medico} el {self.fecha} a las {self.hora}"

