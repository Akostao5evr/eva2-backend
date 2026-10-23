from django import forms
from gestion.models import Funcionario, Delegacion, Cargo, ItemMeta
from .models import Actividad, TipoAtencion, SubAtencion, Delegacion

# Si tu modelo se llama Actividad o Atencion, usa el que corresponda:
try:
    from .models import Actividad as ModeloAtencion
except ImportError:
    from .models import Atencion as ModeloAtencion

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
        fields = ['nombre', 'descripcion', 'estado']

class TipoAtencionForm(forms.ModelForm):
    class Meta:
        model = TipoAtencion
        fields = ['nombre', 'descripcion', 'estado']

class SubAtencionForm(forms.ModelForm):
    class Meta:
        model = SubAtencion
        fields = ['nombre', 'tipo_atencion', 'estado']

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['solicitante', 'delegacion', 'funcionario', 'tipo_atencion', 'sub_atencion', 'descripcion']
        widgets = {
            'solicitante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar por identificador o nombre...', 'required': 'required'}),
            'delegacion': forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
            'funcionario': forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
            'tipo_atencion': forms.Select(attrs={'class': 'form-select', 'id': 'selectTipo', 'required': 'required'}),
            'sub_atencion': forms.Select(attrs={'class': 'form-select', 'id': 'selectSub', 'required': 'required'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describa la solicitud y los antecedentes necesarios.', 'required': 'required'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo_atencion'].queryset = TipoAtencion.objects.filter(estado=True)
        self.fields['delegacion'].queryset = Delegacion.objects.filter(estado=True)
        self.fields['funcionario'].queryset = Funcionario.objects.filter(estado=True)
        # Permite validar cualquier subatención activa enviada dinámicamente
        self.fields['sub_atencion'].queryset = SubAtencion.objects.filter(estado=True)
        self.fields['tipo_atencion'].empty_label = "Seleccione Tipo de Atención..."
        self.fields['sub_atencion'].empty_label = "Seleccione Sub Atención..."

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_atencion')
        sub = cleaned_data.get('sub_atencion')
        # Validación de integridad de catálogo en el servidor (Pauta C6)
        if tipo and sub and sub.tipo_atencion_id != tipo.id:
            self.add_error('sub_atencion', 'La Sub Atención seleccionada no pertenece al Tipo de Atención indicado.')
        return cleaned_data