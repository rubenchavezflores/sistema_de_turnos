from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('consultar-paciente/', views.consultar_paciente, name='consultar_paciente'),
    path('paciente/modificar/<str:dni>/', views.modificar_paciente, name='modificar_paciente'),
    path('registrar-paciente/<str:dni>/', views.registrar_paciente, name='registrar_paciente'),
    path('otorgar_turno/<int:medico_id>/', views.otorgar_turno, name='otorgar_turno'),
    
]
