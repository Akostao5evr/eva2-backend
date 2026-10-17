from django.contrib import admin
from .models import Delegacion, Cargo, Funcionario, ItemMeta

@admin.register(Delegacion)
class DelegacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'nombre', 'comuna', 'estado')
    search_fields = ('codigo', 'nombre')

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'nombre', 'alcance', 'estado')
    search_fields = ('codigo', 'nombre')

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'apellido', 'correo', 'delegacion', 'cargo', 'estado')
    list_filter = ('delegacion', 'cargo', 'estado')
    search_fields = ('rut', 'nombre', 'apellido', 'correo')

@admin.register(ItemMeta)
class ItemMetaAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'nombre', 'estado')
    list_filter = ('estado',)
    search_fields = ('codigo', 'nombre')