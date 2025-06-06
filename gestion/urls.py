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
]
