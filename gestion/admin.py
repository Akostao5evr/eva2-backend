from django.contrib import admin
from .models import Delegacion, Cargo, Funcionario

# Register your models here.

@admin.register(Delegacion)
class DelegacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'estado')
    search_fields = ('nombre',)

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'apellido', 'delegacion', 'cargo')
    list_filter = ('delegacion', 'cargo')
    search_fields = ('rut', 'nombre', 'apellido')