from django.db import models
from datetime import date
from django.db import models


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
    dia = models.CharField(max_length=10, choices=DIAS_SEMANA)
    horario_inicio = models.TimeField()
    horario_fin = models.TimeField()
    intervalo_minutos = models.IntegerField()

    def __str__(self):
        return f"{self.medico} - {self.get_dia_display()} de {self.horario_inicio.strftime('%H:%M')} a {self.horario_fin.strftime('%H:%M')} cada {self.intervalo_minutos} min"

    def clean(self):
        # Validar que horario_fin sea posterior a horario_inicio
        if self.horario_fin <= self.horario_inicio:
            from django.core.exceptions import ValidationError
            raise ValidationError('El horario de fin debe ser posterior al horario de inicio.')

class Paciente(models.Model):
    dni = models.CharField(max_length=20, unique=True)
    sexo = models.CharField(max_length=10, blank=True, null=True)
    apellido = models.CharField(max_length=100)
    nombre = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    @property
    def edad(self):
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - (
                (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None

    telefono_celular = models.CharField(max_length=20, blank=True, null=True)
    telefono_fijo = models.CharField(max_length=20, blank=True, null=True)
    obra_social = models.CharField(max_length=100, blank=True, null=True)
    domicilio = models.CharField(max_length=255, blank=True, null=True)
    localidad = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.dni})"

class Turno(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()

    def __str__(self):
        return f"Turno con {self.medico} el {self.fecha.strftime('%d/%m/%Y')} a las {self.hora.strftime('%H:%M')}"
# gestion/models.py



class HorarioAtencion(models.Model):
    medico = models.ForeignKey('Medico', on_delete=models.CASCADE)
    dia = models.CharField(max_length=10, choices=[
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
    ])
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    def __str__(self):
        return f"{self.medico} - {self.dia}: {self.hora_inicio} a {self.hora_fin}"

class DiaNoLaborable(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateField()
    motivo = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.fecha} - {self.motivo or 'No laborable'}"
