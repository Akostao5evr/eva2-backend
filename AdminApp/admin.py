from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from AdminApp.forms import UsuarioCreationForm as AccountCreationForm
from AdminApp.forms import UsuarioUpdateForm
from AdminApp.models import Cargo, Delegacion, Historial, Rol, Usuario


class AdminUsuarioChangeForm(UsuarioUpdateForm):
	class Meta(UsuarioUpdateForm.Meta):
		fields = UsuarioUpdateForm.Meta.fields + ('is_staff', 'is_superuser')


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
	form = AdminUsuarioChangeForm
	add_form = AccountCreationForm
	fieldsets = (
		(None, {'fields': ('email',)}),
		('Información personal', {'fields': (
			'first_name', 'last_name', 'nombre', 'estado',
			'limite_actividad', 'delegacion', 'cargo', 'roles',
		)}),
		('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
	)
	add_fieldsets = (
		(None, {'classes': ('wide',), 'fields': (
			'email', 'first_name', 'last_name', 'nombre', 'estado',
			'limite_actividad', 'delegacion', 'cargo', 'roles',
			'password1', 'password2',
		)}),
	)
	list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
	list_filter = ('is_staff', 'is_superuser', 'is_active')
	search_fields = ('email', 'first_name', 'last_name')
	ordering = ('email',)
	filter_horizontal = ()


@admin.register(Delegacion)
class DelegacionAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'estado')
	list_filter = ('estado',)
	search_fields = ('nombre',)


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
	list_display = ('nombre', 'estado', 'fecha_inicio', 'fecha_fin')
	list_filter = ('estado',)
	search_fields = ('nombre',)


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
	list_display = ('nombre',)
	search_fields = ('nombre',)




@admin.register(Historial)
class HistorialAdmin(admin.ModelAdmin):
	list_display = ('accion', 'autor', 'periodo', 'fecha_modificacion')
	list_filter = ('accion', 'periodo', 'fecha_modificacion')
	search_fields = ('accion', 'autor__email', 'entidad_afectada')
	readonly_fields = ('fecha_modificacion', 'valor_anterior', 'valor_nuevo')
