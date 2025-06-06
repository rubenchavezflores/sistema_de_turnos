# gestion/utils.py

import re
from datetime import datetime, date, timedelta

from .models import Paciente, Turno

def buscar_paciente_por_dni(dni):
    if not re.match(r'^\d{7,8}$', dni):
        return None
    try:
        return Paciente.objects.filter(dni=dni).first()
    except Exception:
        return None

def generar_intervalos_horarios(hora_inicio_str, hora_fin_str, intervalo_minutos):
    try:
        from datetime import time
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()

        intervalos = []
        dt_inicio = datetime.combine(date.today(), hora_inicio)
        dt_fin = datetime.combine(date.today(), hora_fin)

        current = dt_inicio
        while current + timedelta(minutes=intervalo_minutos) <= dt_fin:
            intervalos.append(current.strftime('%H:%M'))
            current += timedelta(minutes=intervalo_minutos)

        return intervalos

    except ValueError:
        return []

def generar_intervalos_turnos(medico, fecha):
    dias_config = medico.dias_atencion.values(
        'dia', 'horario_inicio', 'horario_fin', 'intervalo_minutos'
    )

    dia_semana = fecha.weekday()
    config_del_dia = None
    for d in dias_config:
        if d['dia'] == dia_semana:
            config_del_dia = d
            break

    if not config_del_dia:
        return []

    intervalos = generar_intervalos_horarios(
        config_del_dia['horario_inicio'],
        config_del_dia['horario_fin'],
        config_del_dia['intervalo_minutos']
    )

    fecha_iso = fecha.isoformat()
    turnos_ocupados = Turno.objects.filter(
        medico=medico,
        fecha_hora__date=fecha
    ).values_list('fecha_hora__time', flat=True)

    lista_turnos = []
    for hora_str in intervalos:
        hora_obj = datetime.strptime(hora_str, "%H:%M").time()
        ocupado = hora_obj in turnos_ocupados

        lista_turnos.append({
            'hora': hora_str,
            'ocupado': ocupado,
            'disponible': not ocupado,
            'fecha_iso': fecha_iso
        })

    return lista_turnos
