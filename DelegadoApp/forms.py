from django import forms

from AdminApp.models import Usuario
from CoordinadorApp.models import Periodo
from DelegadoApp.models import Compromiso
from config.forms import BootstrapFormMixin


class CompromisoForm(BootstrapFormMixin, forms.ModelForm):
    periodo = forms.ModelChoiceField(
        queryset=Periodo.objects.filter(estado=Periodo.Estado.ABIERTO),
        label='Período de agenda',
    )

    class Meta:
        model = Compromiso
        fields = (
            'periodo', 'descripcion', 'solicitante', 'territorio', 'fecha',
            'responsable', 'estado', 'observaciones', 'genera_puntaje',
        )
        labels = {
            'descripcion': 'Compromiso',
            'solicitante': 'Solicitante',
            'territorio': 'Territorio',
            'fecha': 'Fecha comprometida',
            'responsable': 'Responsables',
            'estado': 'Estado',
            'observaciones': 'Observaciones',
        }
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 2}),
            'responsable': forms.SelectMultiple(attrs={'size': 4}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        delegation = user.delegacion_actual
        if delegation:
            self.fields['responsable'].queryset = Usuario.objects.filter(
                usuariodelegacion__delegacion=delegation.delegacion,
                usuariodelegacion__fecha_fin__isnull=True,
                is_active=True,
            ).distinct().order_by('email')
        else:
            self.fields['responsable'].queryset = Usuario.objects.none()
        self.fields['responsable'].help_text = 'Selecciona al menos un responsable.'
        if self.instance and self.instance.agenda_id:
            self.fields['periodo'].initial = self.instance.agenda.periodo_id


class CompromisoEstadoForm(BootstrapFormMixin, forms.Form):
    estado = forms.ChoiceField(choices=Compromiso.Estado.choices, label='Actualizar estado')