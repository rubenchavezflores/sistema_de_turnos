# views.py - Importaciones limpias y ordenadas

from datetime import datetime, timedelta, time, date
from calendar import monthrange

from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import PacienteForm
from .forms import DiaNoLaborableForm

from .models import Especialidad,Medico, Paciente, Turno, HorarioAtencion,DiaNoLaborable

import calendar

# Mapeo de nombre de día a weekday int
DIA_A_INT = {
    'LUNES': 0, 'MARTES': 1, 'MIÉRCOLES': 2, 'MIERCOLES': 2,
    'JUEVES': 3, 'VIERNES': 4, 'SÁBADO': 5, 'SABADO': 5, 'DOMINGO': 6,
}

def inicio(request):
    especialidades = Especialidad.objects.all()
    medicos = Medico.objects.all()
    resultados = None

    if request.method == 'POST':
        buscar_por = request.POST.get('buscar_por')

        if buscar_por == 'especialidad':
            especialidad_id = request.POST.get('especialidad')
            if especialidad_id:
                resultados = Medico.objects.filter(especialidad_id=especialidad_id)
            else:
                resultados = Medico.objects.none()
        elif buscar_por == 'medico':
            medico_id = request.POST.get('medico')
            if medico_id:
                resultados = Medico.objects.filter(id=medico_id)
            else:
                resultados = Medico.objects.none()

    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'resultados': resultados,
    }
    return render(request, 'gestion/inicio.html', context)


def otorgar_turno(request, medico_id):
    medico = get_object_or_404(Medico, id=medico_id)
    hoy = timezone.now().date()

    mes = int(request.GET.get('mes', hoy.month))
    anio = int(request.GET.get('anio', hoy.year))
    fecha_str = request.GET.get('fecha')
    dni = request.GET.get('dni')

    fecha_seleccionada = None
    paciente = None

    if fecha_str:
        try:
            fecha_seleccionada = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            fecha_seleccionada = None

    if dni:
        paciente = Paciente.objects.filter(dni=dni).first()

    dias_atencion = HorarioAtencion.objects.filter(medico=medico)
    dias_mostrados = [
        {
            'dia': d.get_dia_display(),
            'numero_dia': d.dia,
            'horario_inicio': d.hora_inicio.strftime("%H:%M"),
            'horario_fin': d.hora_fin.strftime("%H:%M"),
            'intervalo': d.intervalo_minutos,
        }
        for d in dias_atencion
    ]

    primer_dia_mes = datetime(anio, mes, 1).date()
    _, dias_en_mes = monthrange(anio, mes)
    primer_lunes = primer_dia_mes - timedelta(days=primer_dia_mes.weekday())

    # ** Obtener días no laborables para este médico **
    dias_no_laborables = set(
        DiaNoLaborable.objects.filter(medico=medico).values_list('fecha', flat=True)
    )

    calendario = []

    for i in range(42):  # 6 semanas x 7 días
        dia = primer_lunes + timedelta(days=i)
        es_del_mes = dia.month == mes
        atiende = dias_atencion.filter(dia=dia.weekday()).exists()

        es_no_laborable = dia in dias_no_laborables  # <= chequeo si día está en no laborables

        calendario.append({
            'fecha': dia,
            'es_del_mes': es_del_mes,
            'atiende': atiende,
            'es_no_laborable': es_no_laborable,  # agrego campo para usar en template
        })

    matriz_turnos = []
    if fecha_seleccionada:
        dia_semana = fecha_seleccionada.weekday()
        horarios = dias_atencion.filter(dia=dia_semana)

        for horario in horarios:
            hora_inicio = datetime.combine(fecha_seleccionada, horario.hora_inicio)
            hora_fin = datetime.combine(fecha_seleccionada, horario.hora_fin)
            intervalo = timedelta(minutes=horario.intervalo_minutos)

            hora_actual = hora_inicio
            while hora_actual < hora_fin:
                hora_time = hora_actual.time()
                turno_existente = Turno.objects.filter(
                    medico=medico,
                    fecha=fecha_seleccionada,
                    hora=hora_time
                ).first()

                matriz_turnos.append({
                    'hora': hora_time.strftime("%H:%M"),
                    'ocupado': turno_existente is not None
                })

                hora_actual += intervalo

    if request.method == "POST" and request.POST.get('accion') == 'reservar_turno':
        fecha = request.POST.get('fecha')
        hora_str = request.POST.get('hora')
        dni_post = request.POST.get('dni')
        paciente = Paciente.objects.filter(dni=dni_post).first()

        if paciente:
            try:
                fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
                hora_time = datetime.strptime(hora_str, "%H:%M").time()
            except ValueError:
                messages.error(request, "Fecha u hora inválida.")
                return redirect(request.path)

            ya_ocupado = Turno.objects.filter(medico=medico, fecha=fecha_dt, hora=hora_time).exists()

            if not ya_ocupado:
                Turno.objects.create(
                    medico=medico,
                    paciente=paciente,
                    fecha=fecha_dt,
                    hora=hora_time,
                )
                messages.success(request, f"Turno asignado a {paciente.apellido}, {paciente.nombre} el {fecha_dt.strftime('%d/%m/%Y')} a las {hora_str}.")
                return redirect(request.path + f"?mes={mes}&anio={anio}&fecha={fecha}&dni={dni_post}")
            else:
                messages.error(request, "Este turno ya fue asignado.")
        else:
            messages.error(request, "Paciente no encontrado.")

    contexto = {
        'medico': medico,
        'mes': mes,
        'anio': anio,
        'mes_anterior': (mes - 1) if mes > 1 else 12,
        'anio_anterior': (anio - 1) if mes == 1 else anio,
        'mes_siguiente': (mes + 1) if mes < 12 else 1,
        'anio_siguiente': (anio + 1) if mes == 12 else anio,
        'fecha_seleccionada': fecha_seleccionada,
        'calendario': calendario,
        'dias_mostrados': dias_mostrados,
        'matriz_turnos': matriz_turnos,
        'dni': dni,
        'paciente': paciente,
        'numero_dia_seleccionado': fecha_seleccionada.weekday() if fecha_seleccionada else None,
    }

    return render(request, 'gestion/otorgar_turno.html', contexto)


def registrar_paciente(request, dni):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inicio')
    else:
        form = PacienteForm(initial={'dni': dni})
    return render(request, 'gestion/registrar_paciente.html', {'form': form})


def consultar_paciente(request):
    dni = request.GET.get('dni')
    paciente = Paciente.objects.filter(dni=dni).first() if dni else None
    return render(request, 'gestion/consultar_paciente.html', {
        'dni': dni,
        'paciente': paciente
    })


def modificar_paciente(request, dni):
    paciente = get_object_or_404(Paciente, dni=dni)
    if request.method == 'POST':
        for campo in ['sexo', 'apellido', 'nombre', 'fecha_nacimiento', 'telefono_celular',
                      'telefono_fijo', 'obra_social', 'domicilio', 'localidad']:
            setattr(paciente, campo, request.POST.get(campo))
        paciente.save()
        return redirect('inicio')
    return render(request, 'gestion/modificar_paciente.html', {'paciente': paciente})


def tabla_turnos(request):
    horarios = ['08:00', '08:30', '09:00', '09:30']
    turnos = [
        {'paciente': 'Juan Pérez', 'turnos': ['✔️', '', '', '']},
        {'paciente': 'Ana López', 'turnos': ['', '✔️', '', '']},
        {'paciente': 'Carlos Ruiz', 'turnos': ['', '', '✔️', '']},
    ]
    return render(request, 'gestion/tabla_turnos.html', {
        'horarios': horarios,
        'turnos': turnos
    })


def generar_calendario(medico, anio, mes):
    calendario = []
    primer_dia = date(anio, mes, 1)
    dia_inicio = primer_dia - timedelta(days=primer_dia.weekday())  # lunes previo
    dia_actual = dia_inicio

    dias_atencion = [d.dia.upper() for d in medico.dias.all()]  # ['LUNES', 'MARTES', ...]

    for _ in range(6):
        semana = []
        for _ in range(7):
            nombre_dia = calendar.day_name[dia_actual.weekday()].upper()
            semana.append({
                'fecha': dia_actual,
                'es_del_mes': dia_actual.month == mes,
                'atiende': nombre_dia in dias_atencion
            })
            dia_actual += timedelta(days=1)
        calendario.append(semana)

    return calendario

@login_required
def crear_licencia(request):
    if request.method == 'POST':
        form = DiaNoLaborableForm(request.POST)
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
            medico = form.cleaned_data['medico']

            if DiaNoLaborable.objects.filter(fecha=fecha, medico=medico).exists():
                messages.warning(request, 'Ese día ya está marcado como no laborable.')
            else:
                form.save()
                messages.success(request, 'Día marcado como no laborable correctamente.')
            return redirect('crear_licencia')
    else:
        form = DiaNoLaborableForm()

    return render(request, 'crear_licencia.html', {'form': form})