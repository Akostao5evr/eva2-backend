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
            'solicitante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Pérez Morales', 'required': 'required'}),
            'delegacion': forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
            'funcionario': forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
            'tipo_atencion': forms.Select(attrs={'class': 'form-select', 'id': 'select-tipo', 'required': 'required'}),
            'sub_atencion': forms.Select(attrs={'class': 'form-select', 'id': 'select-subatencion', 'required': 'required'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalle de la solicitud o atención ciudadana...', 'required': 'required'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar solo registros activos
        self.fields['tipo_atencion'].queryset = TipoAtencion.objects.filter(estado=True)
        self.fields['delegacion'].queryset = Delegacion.objects.filter(estado=True)
        self.fields['funcionario'].queryset = Funcionario.objects.filter(estado=True)
        # Inicialmente vacío o filtrado si viene en POST
        if 'tipo_atencion' in self.data:
            try:
                tipo_id = int(self.data.get('tipo_atencion'))
                self.fields['sub_atencion'].queryset = SubAtencion.objects.filter(tipo_atencion_id=tipo_id, estado=True)
            except (ValueError, TypeError):
                self.fields['sub_atencion'].queryset = SubAtencion.objects.none()
        elif self.instance.pk and self.instance.tipo_atencion:
            self.fields['sub_atencion'].queryset = self.instance.tipo_atencion.subatenciones.filter(estado=True)
        else:
            self.fields['sub_atencion'].queryset = SubAtencion.objects.none()