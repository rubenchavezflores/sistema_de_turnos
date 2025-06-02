from django import forms
from .models import Paciente

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['dni', 'sexo', 'apellido', 'nombre', 'fecha_nacimiento', 'telefono_celular', 'telefono_fijo', 'obra_social', 'domicilio', 'localidad']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'dni': forms.TextInput(attrs={'readonly': 'readonly'}),
        }
