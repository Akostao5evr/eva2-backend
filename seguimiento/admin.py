from django.contrib import admin
from .models import Actividad, Evidencia, CompromisoTicket, TipoAtencion, SubAtencion

@admin.register(TipoAtencion)
class TipoAtencionAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'nombre', 'estado')
    list_filter = ('estado',)
    search_fields = ('codigo', 'nombre')

@admin.register(SubAtencion)
class SubAtencionAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'nombre', 'tipo_atencion', 'estado')
    list_filter = ('tipo_atencion', 'estado')
    search_fields = ('codigo', 'nombre')

@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('codigo_verificador', 'solicitante', 'tipo_atencion', 'sub_atencion', 'funcionario', 'delegacion', 'fecha_registro', 'estado')
    list_filter = ('estado', 'delegacion', 'tipo_atencion')
    search_fields = ('codigo_verificador', 'solicitante', 'descripcion')

@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ('actividad', 'observacion')

@admin.register(CompromisoTicket)
class CompromisoTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'sector', 'delegacion', 'funcionario_asignado', 'fecha_limite', 'estado_color')
    list_filter = ('estado_color', 'delegacion')
    search_fields = ('sector', 'solicitante')