from django.contrib import admin
from django import forms
from .models import Especialidad, Medico, DiaAtencion, Paciente, Turno

class DiaAtencionInlineForm(forms.ModelForm):
    class Meta:
        model = DiaAtencion
        fields = '__all__'
        widgets = {
            'horario_inicio': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'horario_fin': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
        }

class DiaAtencionInline(admin.TabularInline):
    model = DiaAtencion
    form = DiaAtencionInlineForm  # <-- acá le decís que use el formulario con TimeInput
    extra = 1

@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre', 'especialidad')
    inlines = [DiaAtencionInline]

admin.site.register(Especialidad)
admin.site.register(Paciente)
admin.site.register(Turno)



