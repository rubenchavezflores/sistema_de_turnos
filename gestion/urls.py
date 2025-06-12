from django.urls import path
from . import views
from .views import tabla_turnos

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('otorgar_turno/<int:medico_id>/', views.otorgar_turno, name='otorgar_turno'),
    path('registrar_paciente/<str:dni>/', views.registrar_paciente, name='registrar_paciente'),
    path('consultar_paciente/', views.consultar_paciente, name='consultar_paciente'),
    path('modificar_paciente/<str:dni>/', views.modificar_paciente, name='modificar_paciente'),
    path('tabla_turnos/', views.tabla_turnos, name='tabla_turnos'),
    path('crear_licencia/', views.crear_licencia, name='crear_licencia'),
    path('buscar/especialidad/', views.buscar_por_especialidad, name='buscar_por_especialidad'),
    path('buscar/apellido/', views.buscar_por_apellido, name='buscar_por_apellido'),
    path('verificar-dni/', views.verificar_dni, name='verificar_dni'),
    path('buscar_paciente_ajax/', views.buscar_paciente_ajax, name='buscar_paciente_ajax'),


]
