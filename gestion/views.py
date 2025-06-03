from django.shortcuts import render, get_object_or_404, redirect
from .models import Especialidad, Medico, Paciente, Turno
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.contrib import messages
from .forms import PacienteForm
from datetime import datetime, timedelta, date

def inicio(request):
    especialidades = Especialidad.objects.all()
    medicos = Medico.objects.all()
    resultados = None

    if request.method == 'POST':
        buscar_por = request.POST.get('buscar_por')

        if buscar_por == 'especialidad':
            especialidad_id = request.POST.get('especialidad')
            if especialidad_id:  # <-- verificar que no esté vacío
                resultados = Medico.objects.filter(especialidad_id=especialidad_id)
            else:
                resultados = Medico.objects.none()  # o mostrar todos o mensaje

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




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from datetime import date, timedelta, datetime
from django.utils.dateparse import parse_date
from .models import Medico, Paciente, Turno

def otorgar_turno(request, medico_id):
    medico = get_object_or_404(Medico, id=medico_id)
    dni = request.POST.get('dni')
    paciente = None
    turnos_disponibles = []

    # Buscar paciente si se ingresó DNI
    if dni:
        try:
            paciente = Paciente.objects.get(dni=dni)
        except Paciente.DoesNotExist:
            paciente = None

    hoy = date.today()
    dias_semana_atencion = list(medico.dias_atencion.values('dia', 'horario_inicio', 'horario_fin', 'intervalo_minutos'))

    fechas_atencion = []
    for i in range(14):
        dia = hoy + timedelta(days=i)
        for d in dias_semana_atencion:
            if dia.weekday() == d['dia']:
                fechas_atencion.append({
                    'fecha': dia,
                    'hora_inicio': d['horario_inicio'],
                    'hora_fin': d['horario_fin'],
                    'intervalo': d['intervalo_minutos'],
                })

    for dia in fechas_atencion:
        fecha = dia['fecha']
        hora_inicio = datetime.strptime(dia['hora_inicio'], '%H:%M')
        hora_fin = datetime.strptime(dia['hora_fin'], '%H:%M')
        intervalo = dia['intervalo']

        intervalos = []
        current = hora_inicio
        while current + timedelta(minutes=intervalo) <= hora_fin:
            hora_str = current.strftime('%H:%M')
            intervalos.append(hora_str)
            current += timedelta(minutes=intervalo)

        turnos_disponibles.append({
            'fecha': fecha.strftime('%A %d/%m/%Y'),
            'fecha_iso': fecha.isoformat(),
            'intervalos': intervalos,
        })

    fechas = [td['fecha_iso'] for td in turnos_disponibles]
    turnos_ocupados = Turno.objects.filter(medico=medico, fecha__in=fechas).values_list('fecha', 'hora')
    ocupados_set = set((str(t[0]), t[1]) for t in turnos_ocupados)

    for dia in turnos_disponibles:
        nuevos_intervalos = []
        for hora in dia['intervalos']:
            ocupado = (dia['fecha_iso'], hora) in ocupados_set
            nuevos_intervalos.append({'hora': hora, 'ocupado': ocupado})
        dia['intervalos'] = nuevos_intervalos

    if request.method == 'POST' and paciente:
        fecha_str = request.POST.get('fecha')
        hora = request.POST.get('hora')

        if fecha_str and hora:
            fecha_obj = parse_date(fecha_str)
            existe_turno = Turno.objects.filter(medico=medico, fecha=fecha_obj, hora=hora).exists()
            if existe_turno:
                messages.error(request, 'El turno ya está ocupado, por favor elija otro horario.')
            else:
                Turno.objects.create(medico=medico, paciente=paciente, fecha=fecha_obj, hora=hora)
                messages.success(request, f'Turno asignado para {fecha_obj} a las {hora}.')
                return redirect('inicio')
        else:
            messages.error(request, 'Debe seleccionar fecha y hora para el turno.')

    horas_unicas = []
    if turnos_disponibles:
        horas_unicas = [intervalo['hora'] for intervalo in turnos_disponibles[0]['intervalos']]

    matriz_turnos = []
    for i, hora in enumerate(horas_unicas):
        fila = {'hora': hora, 'celdas': []}
        for dia in turnos_disponibles:
            intervalo = dia['intervalos'][i]
            fila['celdas'].append({
                'fecha': dia['fecha'],
                'fecha_iso': dia['fecha_iso'],
                'hora': intervalo['hora'],
                'ocupado': intervalo['ocupado'],
            })
        matriz_turnos.append(fila)

    context = {
        'medico': medico,
        'dni': dni,
        'paciente': paciente,
        'turnos_disponibles': turnos_disponibles,
        'fechas': [dia['fecha'] for dia in turnos_disponibles],
        'horas_unicas': horas_unicas,
        'matriz_turnos': matriz_turnos,
    }

    return render(request, 'gestion/otorgar_turno.html', context)


def consultar_paciente(request):
    paciente = None
    dni = request.GET.get('dni')

    if dni:
        try:
            paciente = Paciente.objects.get(dni=dni)
        except Paciente.DoesNotExist:
            paciente = None

    return render(request, 'gestion/consultar_paciente.html', {
        'paciente': paciente,
        'dni': dni
    })

def registrar_paciente(request, dni):
    if request.method == 'POST':
        # Verificar si ya existe un paciente con ese DNI
        if Paciente.objects.filter(dni=dni).exists():
            messages.error(request, 'Ya existe un paciente registrado con ese DNI.')
            return redirect('consultar_paciente')  # o donde prefieras

        # Si no existe, lo creamos
        paciente = Paciente.objects.create(
            dni=dni,
            sexo=request.POST['sexo'],
            apellido=request.POST['apellido'],
            nombre=request.POST['nombre'],
            fecha_nacimiento=request.POST['fecha_nacimiento'],
            telefono_celular=request.POST.get('telefono_celular', ''),
            telefono_fijo=request.POST.get('telefono_fijo', ''),
            obra_social=request.POST.get('obra_social', ''),
            domicilio=request.POST.get('domicilio', ''),
            localidad=request.POST.get('localidad', ''),
        )
        messages.success(request, 'Paciente registrado con éxito.')
        return redirect('inicio')

    return render(request, 'gestion/registrar_paciente.html', {'dni': dni})

def modificar_paciente(request, dni):
    paciente = get_object_or_404(Paciente, dni=dni)

    if request.method == 'POST':
        paciente.sexo = request.POST['sexo']
        paciente.apellido = request.POST['apellido']
        paciente.nombre = request.POST['nombre']
        paciente.fecha_nacimiento = request.POST['fecha_nacimiento']
        paciente.telefono_celular = request.POST.get('telefono_celular', '')
        paciente.telefono_fijo = request.POST.get('telefono_fijo', '')
        paciente.obra_social = request.POST.get('obra_social', '')
        paciente.domicilio = request.POST.get('domicilio', '')
        paciente.localidad = request.POST.get('localidad', '')
        paciente.save()
        messages.success(request, 'Datos del paciente actualizados con éxito.')
        return redirect('consultar_paciente')  # o redirigir a otra vista si preferís

    return render(request, 'gestion/modificar_paciente.html', {'paciente': paciente})

