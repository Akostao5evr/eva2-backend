from django import forms
from gestion.models import Funcionario, Delegacion, Cargo, ItemMeta
from .models import Actividad, TipoAtencion, SubAtencion

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['rut', 'nombre', 'apellido', 'delegacion', 'cargo']

class DelegacionForm(forms.ModelForm):
    class Meta:
        model = Delegacion
        fields = ['nombre', 'direccion', 'estado']

class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ['nombre', 'descripcion']

class ItemMetaForm(forms.ModelForm):
    class Meta:
        model = ItemMeta
        fields = ['codigo', 'nombre', 'descripcion', 'estado']

class TipoAtencionForm(forms.ModelForm):
    class Meta:
        model = TipoAtencion
        fields = ['codigo', 'nombre', 'descripcion', 'estado']

class SubAtencionForm(forms.ModelForm):
    class Meta:
        model = SubAtencion
        fields = ['codigo', 'nombre', 'tipo_atencion', 'estado']

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['funcionario', 'delegacion', 'descripcion', 'estado']