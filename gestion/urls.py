from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('otorgar_turno/<int:medico_id>/', views.otorgar_turno, name='otorgar_turno'),
]
