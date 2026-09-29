from django import forms
from gestion.models import Funcionario
from .models import Actividad

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['rut', 'nombre', 'apellido', 'delegacion', 'cargo']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12.345.678-9'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'delegacion': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.Select(attrs={'class': 'form-select'}),
        }

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['funcionario', 'delegacion', 'descripcion', 'estado']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'delegacion': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describa la actividad...'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }