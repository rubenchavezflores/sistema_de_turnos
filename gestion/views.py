from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from datetime import date, timedelta, datetime
from django.utils.dateparse import parse_date
from .models import Especialidad, Medico, Paciente, Turno
from django.http import HttpResponse
from .forms import PacienteForm
import re

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
    """
    Vista para otorgar turnos a pacientes.
    Genera una matriz de turnos disponibles para las próximas 2 semanas.
    """
    medico = get_object_or_404(Medico, id=medico_id)
    
    # Procesar formulario si es POST
    if request.method == 'POST':
        return procesar_formulario_turno(request, medico)
    
    # Obtener DNI y paciente
    dni = request.GET.get('dni', '').strip()
    paciente = buscar_paciente_por_dni(dni) if dni else None
    
    # Generar fechas de atención
    fechas_atencion = generar_fechas_atencion(medico)
    
    # Generar matriz de turnos
    matriz_turnos = generar_matriz_turnos(medico, fechas_atencion)
    
    # Preparar contexto
    context = {
        'medico': medico,
        'dni': dni,
        'paciente': paciente,
        'matriz_turnos': matriz_turnos,
        'fechas_disponibles': [fecha['fecha_formateada'] for fecha in fechas_atencion],
        'dias_atencion_iso': [fecha['fecha_iso'] for fecha in fechas_atencion],
    }
    
    return render(request, 'gestion/otorgar_turno.html', context)

def buscar_paciente_por_dni(dni):
    """
    Busca un paciente por DNI con validación básica.
    """
    # Validar formato de DNI (solo números, 7-8 dígitos)
    if not re.match(r'^\d{7,8}$', dni):
        return None
    
    try:
        return Paciente.objects.filter(dni=dni).first()
    except Exception:
        return None

def generar_fechas_atencion(medico, dias_adelante=14):
    """
    Genera las fechas de atención del médico para los próximos días.
    """
    hoy = date.today()
    dias_semana_atencion = medico.dias_atencion.values(
        'dia', 'horario_inicio', 'horario_fin', 'intervalo_minutos'
    )
    
    fechas_atencion = []
    
    for i in range(dias_adelante):
        dia = hoy + timedelta(days=i)
        
        # Buscar si el médico atiende ese día de la semana
        for config_dia in dias_semana_atencion:
            if dia.weekday() == config_dia['dia']:
                fechas_atencion.append({
                    'fecha': dia,
                    'fecha_iso': dia.isoformat(),
                    'fecha_formateada': dia.strftime('%A %d/%m/%Y'),
                    'horario_inicio': config_dia['horario_inicio'],
                    'horario_fin': config_dia['horario_fin'],
                    'intervalo_minutos': config_dia['intervalo_minutos'],
                })
                break  # Solo una configuración por día
    
    return fechas_atencion

def generar_intervalos_horarios(hora_inicio_str, hora_fin_str, intervalo_minutos):
    """
    Genera los intervalos de horarios disponibles.
    """
    try:
        # Usar solo time objects para evitar problemas de fecha
        from datetime import time
        
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()
        
        intervalos = []
        
        # Convertir a datetime para hacer cálculos
        dt_inicio = datetime.combine(date.today(), hora_inicio)
        dt_fin = datetime.combine(date.today(), hora_fin)
        
        current = dt_inicio
        while current + timedelta(minutes=intervalo_minutos) <= dt_fin:
            intervalos.append(current.strftime('%H:%M'))
            current += timedelta(minutes=intervalo_minutos)
        
        return intervalos
        
    except ValueError as e:
        # Log del error en producción
        print(f"Error generando intervalos: {e}")
        return []

def generar_matriz_turnos(medico, fechas_atencion):
    """
    Genera la matriz de turnos con disponibilidad.
    """
    if not fechas_atencion:
        return []
    
    # Obtener turnos ya ocupados
    fechas_iso = [fecha['fecha_iso'] for fecha in fechas_atencion]
    turnos_ocupados = Turno.objects.filter(
        medico=medico, 
        fecha__in=fechas_iso
    ).values_list('fecha', 'hora')
    
    ocupados_set = {(str(fecha), hora) for fecha, hora in turnos_ocupados}
    
    # Generar todos los horarios únicos
    todos_los_horarios = set()
    fechas_con_intervalos = []
    
    for fecha in fechas_atencion:
        intervalos = generar_intervalos_horarios(
            fecha['horario_inicio'],
            fecha['horario_fin'],
            fecha['intervalo_minutos']
        )
        
        intervalos_con_disponibilidad = []
        for hora in intervalos:
            ocupado = (fecha['fecha_iso'], hora) in ocupados_set
            intervalos_con_disponibilidad.append({
                'hora': hora,
                'ocupado': ocupado
            })
            todos_los_horarios.add(hora)
        
        fechas_con_intervalos.append({
            **fecha,
            'intervalos': intervalos_con_disponibilidad
        })
    
    # Crear matriz ordenada por horario
    horarios_ordenados = sorted(todos_los_horarios)
    matriz_turnos = []
    
    for hora in horarios_ordenados:
        fila = {
            'hora': hora,
            'celdas': []
        }
        
        for fecha in fechas_con_intervalos:
            # Buscar el intervalo correspondiente a esta hora
            intervalo_encontrado = None
            for intervalo in fecha['intervalos']:
                if intervalo['hora'] == hora:
                    intervalo_encontrado = intervalo
                    break
            
            if intervalo_encontrado:
                fila['celdas'].append({
                    'fecha_formateada': fecha['fecha_formateada'],
                    'fecha_iso': fecha['fecha_iso'],
                    'hora': hora,
                    'ocupado': intervalo_encontrado['ocupado'],
                    'disponible': not intervalo_encontrado['ocupado']
                })
            else:
                # El médico no atiende a esta hora en este día
                fila['celdas'].append({
                    'fecha_formateada': fecha['fecha_formateada'],
                    'fecha_iso': fecha['fecha_iso'],
                    'hora': hora,
                    'ocupado': True,  # Marcamos como ocupado lo que no está disponible
                    'disponible': False,
                    'no_atiende': True
                })
        
        matriz_turnos.append(fila)
    
    return matriz_turnos

def procesar_formulario_turno(request, medico):
    """
    Procesa el formulario de asignación de turno.
    """
    dni = request.POST.get('dni', '').strip()
    fecha_str = request.POST.get('fecha')
    hora = request.POST.get('hora')
    
    # Validaciones
    if not dni:
        messages.error(request, 'Debe ingresar un DNI.')
        return redirect('otorgar_turno', medico_id=medico.id)
    
    paciente = buscar_paciente_por_dni(dni)
    if not paciente:
        messages.error(request, 'No se encontró un paciente con ese DNI.')
        return redirect('otorgar_turno', medico_id=medico.id)
    
    if not fecha_str or not hora:
        messages.error(request, 'Debe seleccionar fecha y hora para el turno.')
        return redirect('otorgar_turno', medico_id=medico.id)
    
    # Procesar fecha
    try:
        fecha_obj = parse_date(fecha_str)
        if not fecha_obj:
            raise ValueError("Fecha inválida")
    except (ValueError, TypeError):
        messages.error(request, 'Formato de fecha inválido.')
        return redirect('otorgar_turno', medico_id=medico.id)
    
    # Verificar que el turno no esté ocupado
    if Turno.objects.filter(medico=medico, fecha=fecha_obj, hora=hora).exists():
        messages.error(request, 'El turno ya está ocupado, por favor elija otro horario.')
        return redirect('otorgar_turno', medico_id=medico.id)
    
    # Verificar que el paciente no tenga otro turno el mismo día con el mismo médico
    if Turno.objects.filter(medico=medico, paciente=paciente, fecha=fecha_obj).exists():
        messages.error(request, 'El paciente ya tiene un turno ese día con este médico.')
        return redirect('otorgar_turno', medico_id=medico.id)
    
    # Crear el turno
    try:
        Turno.objects.create(
            medico=medico,
            paciente=paciente,
            fecha=fecha_obj,
            hora=hora
        )
        messages.success(
            request,
            f'Turno asignado exitosamente para {paciente.nombre} {paciente.apellido} '
            f'el {fecha_obj.strftime("%d/%m/%Y")} a las {hora}.'
        )
        return redirect('inicio')
        
    except Exception as e:
        messages.error(request, 'Error al crear el turno. Intente nuevamente.')
        # En producción, loggear el error
        print(f"Error creando turno: {e}")
        return redirect('otorgar_turno', medico_id=medico.id)


def modificar_paciente(request, dni):
    # Intentamos obtener el paciente por DNI, si no existe da error 404
    paciente = get_object_or_404(Paciente, dni=dni)

    if request.method == 'POST':
        # Aquí procesarías el formulario de modificación (a implementar)
        # Por ahora solo redirigimos o mostramos mensaje
        return HttpResponse(f"Modificación guardada para paciente con DNI: {dni}")

    # Si es GET mostramos un formulario simple (o algo para que no falle)
    return render(request, 'gestion/modificar_paciente.html', {'paciente': paciente})

def registrar_paciente(request, dni):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inicio')  # Cambiá esto por la URL a donde quieras redirigir
    else:
        form = PacienteForm(initial={'dni': dni})
    return render(request, 'gestion/registrar_paciente.html', {'form': form})

def consultar_paciente(request):
    dni = request.GET.get('dni')
    paciente = None
    if dni:
        try:
            paciente = Paciente.objects.get(dni=dni)
        except Paciente.DoesNotExist:
            paciente = None

    contexto = {
        'dni': dni,
        'paciente': paciente,
    }
    return render(request, 'gestion/consultar_paciente.html', contexto)

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