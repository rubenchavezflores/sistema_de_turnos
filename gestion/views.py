# views.py - Importaciones limpias y ordenadas

from datetime import datetime, timedelta, date
from calendar import monthrange, day_name

from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

from .forms import PacienteForm, DiaNoLaborableForm
from .models import Medico, DiaAtencion, Turno, Paciente, DiaNoLaborable, Especialidad

import calendar

import json




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




from datetime import datetime, timedelta
from calendar import monthrange
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone

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

    dias_atencion = DiaAtencion.objects.filter(medico=medico)

    dias_mostrados = [
        {
            'dia': d.get_dia_display(),
            'numero_dia': int(d.dia),
            'horario_inicio': d.horario_inicio.strftime("%H:%M"),
            'horario_fin': d.horario_fin.strftime("%H:%M"),
            'intervalo': d.intervalo_minutos,
        }
        for d in dias_atencion
    ]

    primer_dia_mes = datetime(anio, mes, 1).date()
    _, dias_en_mes = monthrange(anio, mes)
    primer_lunes = primer_dia_mes - timedelta(days=primer_dia_mes.weekday())

    dias_no_laborables = set(
        DiaNoLaborable.objects.filter(medico=medico).values_list('fecha', flat=True)
    )

    calendario = []

    for i in range(42):
        dia = primer_lunes + timedelta(days=i)
        es_del_mes = dia.month == mes
        atiende = dias_atencion.filter(dia=str(dia.weekday())).exists()
        es_no_laborable = dia in dias_no_laborables

        calendario.append({
            'fecha': dia,
            'es_del_mes': es_del_mes,
            'atiende': atiende,
            'es_no_laborable': es_no_laborable,
        })

    matriz_turnos = []
    turnos_ocupados_dict = {}

    if fecha_seleccionada:
        dia_semana = str(fecha_seleccionada.weekday())
        horarios = dias_atencion.filter(dia=dia_semana)

        for horario in horarios:
            hora_inicio = datetime.combine(fecha_seleccionada, horario.horario_inicio)
            hora_fin = datetime.combine(fecha_seleccionada, horario.horario_fin)
            intervalo = timedelta(minutes=horario.intervalo_minutos)

            hora_actual = hora_inicio
            while hora_actual < hora_fin:
                hora_time = hora_actual.time()
                turno_existente = Turno.objects.filter(
                    medico=medico,
                    fecha=fecha_seleccionada,
                    hora=hora_time
                ).select_related('paciente').first()

                ocupado = turno_existente is not None
                matriz_turnos.append({
                    'hora': hora_time.strftime("%H:%M"),
                    'ocupado': ocupado
                })

                if ocupado:
                    turnos_ocupados_dict[hora_time.strftime("%H:%M")] = {
                        'apellido': turno_existente.paciente.apellido,
                        'nombre': turno_existente.paciente.nombre,
                        'sexo': turno_existente.paciente.sexo,
                        'edad': turno_existente.paciente.edad,
                        'obra_social': turno_existente.paciente.obra_social,
                        'localidad': turno_existente.paciente.localidad,
                    }

                hora_actual += intervalo

        # Si no se está buscando por DNI, mostrar el paciente del turno ya asignado
        if not dni:
            turno_existente = Turno.objects.filter(
                medico=medico,
                fecha=fecha_seleccionada
            ).select_related('paciente').first()

            if turno_existente:
                paciente = turno_existente.paciente

    if request.method == "POST" and request.POST.get('accion') == 'reservar_turno':
        fecha_post = request.POST.get('fecha')
        hora_str = request.POST.get('hora')
        dni_post = request.POST.get('dni')
        paciente_post = Paciente.objects.filter(dni=dni_post).first()

        if paciente_post:
            try:
                fecha_dt = datetime.strptime(fecha_post, "%Y-%m-%d").date()
                hora_time = datetime.strptime(hora_str, "%H:%M").time()
            except ValueError:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Fecha u hora inválida.'}, status=400)
                messages.error(request, "Fecha u hora inválida.")
                return redirect(request.path)

            ya_ocupado = Turno.objects.filter(medico=medico, fecha=fecha_dt, hora=hora_time).exists()

            if not ya_ocupado:
                Turno.objects.create(
                    medico=medico,
                    paciente=paciente_post,
                    fecha=fecha_dt,
                    hora=hora_time,
                )
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'mensaje': 'Turno otorgado con éxito.'})
                messages.success(request, f"Turno asignado a {paciente_post.apellido}, {paciente_post.nombre} el {fecha_dt.strftime('%d/%m/%Y')} a las {hora_str}.")
                query_params = f"?mes={mes}&anio={anio}"
                if fecha_post and dni_post:
                    query_params += f"&fecha={fecha_post}&dni={dni_post}"
                return redirect(request.path + query_params)
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'Este turno ya fue asignado.'}, status=400)
                messages.error(request, "Este turno ya fue asignado.")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Paciente no encontrado.'}, status=400)
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
        'turnos_ocupados_dict': turnos_ocupados_dict,
        'dni': dni,
        'paciente': paciente,
        'numero_dia_seleccionado': fecha_seleccionada.weekday() if fecha_seleccionada else None,
    }

    return render(request, 'gestion/otorgar_turno.html', contexto)



def registrar_paciente(request, dni=None):
    if request.method == 'POST':
        dni = request.POST.get('dni')
        if Paciente.objects.filter(dni=dni).exists():
            messages.error(request, "⚠️ Ya existe un paciente con ese DNI.")
            return render(request, 'gestion/registrar_paciente.html', {'form': PacienteForm(request.POST)})

        # Convertir a mayúsculas
        apellido1 = request.POST.get('apellido1', '').strip().upper()
        apellido2 = request.POST.get('apellido2', '').strip().upper()
        nombres = request.POST.get('nombres', '').strip().upper()

        data = request.POST.copy()
        data['apellido'] = f"{apellido1} {apellido2}".strip()
        data['nombre'] = nombres
        data['obra_social'] = data.get('obra_social', '').upper()
        data['domicilio'] = data.get('domicilio', '').upper()
        data['localidad'] = data.get('localidad', '').upper()

        form = PacienteForm(data)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Paciente registrado con éxito.")
            return redirect('inicio')
        else:
            messages.error(request, "❌ Error al registrar paciente. Verifique los datos ingresados.")
    else:
        form = PacienteForm()
    return render(request, 'gestion/registrar_paciente.html', {'form': form})




def consultar_paciente(request):
    dni = request.GET.get('dni')
    paciente = Paciente.objects.filter(dni=dni).first() if dni else None

    if paciente:
        # Convertimos todos los datos a mayúsculas para mostrar
        paciente.nombre = paciente.nombre.upper()
        paciente.apellido = paciente.apellido.upper()
        paciente.obra_social = paciente.obra_social.upper() if paciente.obra_social else ''
        paciente.localidad = paciente.localidad.upper() if paciente.localidad else ''
        paciente.domicilio = paciente.domicilio.upper() if paciente.domicilio else ''

    return render(request, 'gestion/consultar_paciente.html', {
        'dni': dni,
        'paciente': paciente
    })





def modificar_paciente(request, dni):
    paciente = get_object_or_404(Paciente, dni=dni)

    # Separar apellidos en la vista
    apellidos = paciente.apellido.split(' ') if paciente.apellido else ['', '']
    apellido1 = apellidos[0]
    apellido2 = apellidos[1] if len(apellidos) > 1 else ''

    if request.method == 'POST':
        paciente.sexo = request.POST.get('sexo')
        # Unir apellidos antes de guardar
        apellido1_post = request.POST.get('apellido1', '').strip()
        apellido2_post = request.POST.get('apellido2', '').strip()
        paciente.apellido = apellido1_post + (' ' + apellido2_post if apellido2_post else '')
        paciente.nombre = request.POST.get('nombres')
        paciente.fecha_nacimiento = request.POST.get('fecha_nacimiento')
        paciente.telefono_celular = request.POST.get('telefono_celular')
        paciente.telefono_fijo = request.POST.get('telefono_fijo')
        paciente.obra_social = request.POST.get('obra_social')
        paciente.domicilio = request.POST.get('domicilio')
        paciente.localidad = request.POST.get('localidad')
        paciente.save()
        return redirect('inicio')  # O la url que quieras

    context = {
        'paciente': paciente,
        'apellido1': apellido1,
        'apellido2': apellido2,
    }
    return render(request, 'gestion/modificar_paciente.html', context)



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

def buscar_por_especialidad(request):
    especialidades = Especialidad.objects.all()
    resultados = None
    if request.method == "POST":
        especialidad_id = request.POST.get('especialidad')
        if especialidad_id:
            resultados = Medico.objects.filter(especialidad_id=especialidad_id)
    return render(request, 'gestion/buscar_por_especialidad.html', {
        'especialidades': especialidades,
        'resultados': resultados,
    })

def buscar_por_apellido(request):
    medicos = Medico.objects.all()
    resultados = None
    if request.method == "POST":
        apellido = request.POST.get('apellido', '').strip()
        if apellido:
            resultados = Medico.objects.filter(apellido__icontains=apellido)
    return render(request, 'gestion/buscar_por_apellido.html', {
        'medicos': medicos,
        'resultados': resultados,
    })

from django.views.decorators.http import require_GET
from django.http import JsonResponse
from .models import Paciente

@require_GET
def verificar_dni(request):
    try:
        dni = request.GET.get('dni', None)
        existe = False
        if dni:
            existe = Paciente.objects.filter(dni=dni).exists()
        return JsonResponse({'existe': existe})
    except Exception as e:
        print(f"Error en verificar_dni: {e}")
        return JsonResponse({'error': 'Ocurrió un error interno'}, status=500)



def buscar_paciente_ajax(request):
    dni = request.GET.get('dni')
    if not dni:
        return JsonResponse({'existe': False, 'error': 'No se recibió DNI'}, status=400)

    try:
        paciente = Paciente.objects.get(dni=dni)
        data = {
            'existe': True,
            'id': paciente.id,  # ← ESTA LÍNEA ES CLAVE
            'apellido': paciente.apellido,
            'nombre': paciente.nombre,
            'sexo': paciente.sexo,
            'fecha_nacimiento': paciente.fecha_nacimiento.isoformat() if paciente.fecha_nacimiento else None,
            'obra_social': paciente.obra_social or '',
            'localidad': paciente.localidad,
        }
        return JsonResponse(data)
    except Paciente.DoesNotExist:
        return JsonResponse({'existe': False})
    except Exception as e:
        # Si hay otro error inesperado, lo registramos (en consola o logs)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al buscar paciente: {e}")
        print("Error detallado:", e)  # <-- agrega esto
        return JsonResponse({'existe': False, 'error': 'Error interno del servidor'}, status=500)
    
def turnos_por_medico(request, medico_id):
    turnos = Turno.objects.filter(medico_id=medico_id).order_by('fecha', 'hora')
    medico = Medico.objects.get(id=medico_id)
    return render(request, 'turnos_por_medico.html', {'turnos': turnos, 'medico': medico})    


@csrf_exempt
def guardar_turno(request):
    if request.method == 'POST':
        try:
            datos = json.loads(request.body)

            fecha_str = datos.get("fecha")  # Ejemplo: "2025-06-17"
            hora = datos.get("hora")
            medico_id = datos.get("medico")
            paciente_id = datos.get("paciente")

            # Convertir string a objeto datetime.date
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()

            # Validar que no exista un turno en esa fecha/hora para ese médico
            if Turno.objects.filter(fecha=fecha, hora=hora, medico_id=medico_id).exists():
                return JsonResponse({"error": "El turno ya está asignado"}, status=400)

            # Crear el turno
            Turno.objects.create(
                fecha=fecha,
                hora=hora,
                medico_id=medico_id,
                paciente_id=paciente_id,
                estado='otorgado'
            )

            return JsonResponse({"mensaje": "Turno guardado correctamente"})
        except Exception as e:
            print("Error al guardar el turno:", e)
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Método no permitido"}, status=405)

