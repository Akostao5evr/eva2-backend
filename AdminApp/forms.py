from django import forms
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from AdminApp.models import (
    Cargo,
    Delegacion,
    Rol,
    Usuario,
    UsuarioCargo,
    UsuarioDelegacion,
    UsuarioRol,
    _administrator_accounts,
)
from config.forms import BootstrapFormMixin


class UsuarioCreationForm(BootstrapFormMixin, forms.ModelForm):
    delegacion = forms.ModelChoiceField(
        queryset=Delegacion.objects.all(), required=False, label='Delegación',
    )
    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.all(), required=False, label='Cargo',
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=Rol.objects.all(), required=False, label='Roles',
    )
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = (
            'email', 'first_name', 'last_name', 'nombre', 'estado',
            'limite_actividad', 'is_active',
        )
        labels = {
            'email': 'Correo electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'nombre': 'Nombre completo',
            'estado': 'Estado',
            'limite_actividad': 'Límite de actividad',
            'is_active': 'Cuenta activa',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            delegation = self.instance.delegacion_actual
            cargo = self.instance.cargo_actual
            if delegation:
                self.fields['delegacion'].initial = delegation.delegacion
            if cargo:
                self.fields['cargo'].initial = cargo.cargo
            self.fields['roles'].initial = Rol.objects.filter(
                usuariorol__usuario=self.instance,
                usuariorol__fecha_fin__isnull=True,
            )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password1')
        password_confirmation = cleaned_data.get('password2')
        if password and password_confirmation and password != password_confirmation:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        elif password:
            validate_password(password)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if not user.nombre:
            user.nombre = ' '.join(
                value for value in (user.first_name, user.last_name) if value
            )
        if commit:
            with transaction.atomic():
                user.save()
                self._save_assignments(user)
        return user

    def _save_assignments(self, user):
        now = timezone.now()
        delegation = self.cleaned_data.get('delegacion')
        current_delegation = UsuarioDelegacion.objects.filter(
            usuario=user, fecha_fin__isnull=True,
        ).order_by('-fecha_inicio', '-pk').first()
        if (current_delegation.delegacion_id if current_delegation else None) != (
            delegation.pk if delegation else None
        ):
            if current_delegation:
                current_delegation.fecha_fin = now
                current_delegation.save(update_fields=['fecha_fin'])
            if delegation:
                UsuarioDelegacion.objects.create(
                    usuario=user, delegacion=delegation, fecha_inicio=now,
                )

        cargo = self.cleaned_data.get('cargo')
        current_cargo = UsuarioCargo.objects.filter(
            usuario=user, fecha_fin__isnull=True,
        ).order_by('-fecha_inicio', '-pk').first()
        if (current_cargo.cargo_id if current_cargo else None) != (
            cargo.pk if cargo else None
        ):
            if current_cargo:
                current_cargo.fecha_fin = now
                current_cargo.save(update_fields=['fecha_fin'])
            if cargo:
                UsuarioCargo.objects.create(
                    usuario=user, cargo=cargo, fecha_inicio=now,
                )

        selected_roles = set(
            self.cleaned_data.get('roles', Rol.objects.none()).values_list(
                'pk', flat=True,
            )
        )
        current_roles = UsuarioRol.objects.filter(
            usuario=user, fecha_fin__isnull=True,
        )
        current_role_ids = set(current_roles.values_list('rol_id', flat=True))
        current_roles.exclude(rol_id__in=selected_roles).update(fecha_fin=now)
        UsuarioRol.objects.bulk_create([
            UsuarioRol(usuario=user, rol_id=role_id, fecha_inicio=now)
            for role_id in selected_roles - current_role_ids
        ])


class UsuarioUpdateForm(UsuarioCreationForm):
    password1 = forms.CharField(label='Nueva contraseña', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput, required=False)

    class Meta(UsuarioCreationForm.Meta):
        pass

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password1')
        password_confirmation = cleaned_data.get('password2')
        if password != password_confirmation:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        elif password:
            validate_password(password, self.instance)
        if self.instance.pk and self.instance.is_active:
            current_cargo = self.instance.cargo_actual
            was_administrator = self.instance.is_superuser or bool(
                current_cargo
                and current_cargo.cargo.nombre.strip().casefold()
                in {'admin', 'administrador'}
            )
            new_is_superuser = cleaned_data.get(
                'is_superuser', self.instance.is_superuser,
            )
            new_is_active = cleaned_data.get('is_active', self.instance.is_active)
            new_cargo = cleaned_data.get('cargo')
            remains_administrator = new_is_active and (
                new_is_superuser
                or bool(
                    new_cargo
                    and new_cargo.nombre.strip().casefold()
                    in {'admin', 'administrador'}
                )
            )
            if (
                was_administrator
                and not remains_administrator
                and Usuario.objects.filter(is_active=True).filter(
                    _administrator_accounts(),
                ).count() <= 1
            ):
                self.add_error(
                    'cargo',
                    'No se puede quitar el último Administrador activo.',
                )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if not user.nombre:
            user.nombre = ' '.join(
                value for value in (user.first_name, user.last_name) if value
            )
        if commit:
            with transaction.atomic():
                user.save()
                self._save_assignments(user)
        return user