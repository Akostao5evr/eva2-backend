from django.contrib import admin
from .models import Actividad, Evidencia, CompromisoTicket

# Register your models here.

@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ('codigo_verificador', 'funcionario', 'delegacion', 'fecha_registro', 'estado')
    list_filter = ('estado', 'delegacion')
    search_fields = ('codigo_verificador', 'descripcion')

@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ('actividad', 'observacion')

@admin.register(CompromisoTicket)
class CompromisoTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'sector', 'delegacion', 'funcionario_asignado', 'fecha_limite', 'estado_color')
    list_filter = ('estado_color', 'delegacion')
    search_fields = ('sector', 'solicitante')