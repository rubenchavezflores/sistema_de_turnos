from django.shortcuts import render, get_object_or_404, redirect
from .models import Especialidad, Medico, Paciente, Turno
from django.contrib import messages
from django.utils.dateparse import parse_date

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


def otorgar_turno(request, medico_id):
    medico = get_object_or_404(Medico, id=medico_id)
    dias_atencion = medico.dias_atencion.all()  # relación relacionada
    dni = request.POST.get('dni')
    paciente = None

    if request.method == 'POST':
        if 'nombre' in request.POST:
            # Registro nuevo paciente y turno
            paciente = Paciente.objects.create(
                dni=request.POST['dni'],
                nombre=request.POST['nombre'],
                apellido=request.POST['apellido'],
            )
            fecha = parse_date(request.POST['fecha'])
            Turno.objects.create(medico=medico, paciente=paciente, fecha=fecha)
            messages.success(request, 'Turno registrado con éxito.')
            return redirect('inicio')

        elif dni:
            try:
                paciente = Paciente.objects.get(dni=dni)
            except Paciente.DoesNotExist:
                paciente = None

    return render(request, 'gestion/otorgar_turno.html', {
        'medico': medico,
        'dias_atencion': dias_atencion,
        'dni': dni,
        'paciente': paciente,
    })
