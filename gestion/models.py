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


from django.db import models
from datetime import date

class Paciente(models.Model):
    dni = models.CharField(max_length=20, unique=True)
    sexo = models.CharField(max_length=10, blank=True, null=True)
    apellido = models.CharField(max_length=100)
    nombre = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    telefono_celular = models.CharField(max_length=20, blank=True, null=True)
    telefono_fijo = models.CharField(max_length=20, blank=True, null=True)
    obra_social = models.CharField(max_length=100, blank=True, null=True)
    domicilio = models.CharField(max_length=255, blank=True, null=True)
    localidad = models.CharField(max_length=100, blank=True, null=True)

    def edad(self):
        hoy = date.today()
        if self.fecha_nacimiento:
            return hoy.year - self.fecha_nacimiento.year - ((hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.dni})"


class Turno(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()

    def __str__(self):
        return f"Turno con {self.medico} el {self.fecha} a las {self.hora}"

