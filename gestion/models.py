from django.db import models
from django.contrib.auth.models import User

# 1. Delegaciones
class Delegacion(models.Model):
    codigo = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código")
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    direccion = models.CharField(max_length=200, blank=True, null=True, verbose_name="Dirección")
    comuna = models.CharField(max_length=100, default="La Serena", verbose_name="Comuna")
    estado = models.BooleanField(default=True, verbose_name="Estado")

    def __str__(self):
        return f"{self.codigo or ''} - {self.nombre}"

# 2. Roles
class Cargo(models.Model):
    codigo = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código")
    nombre = models.CharField(max_length=100, verbose_name="Rol")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    alcance = models.CharField(max_length=50, default="Autorizado", verbose_name="Alcance")
    estado = models.BooleanField(default=True, verbose_name="Estado")

    def __str__(self):
        return self.nombre

# 3. Usuarios / Funcionarios (Diseño 7 - Pág. 29)
class Funcionario(models.Model):
    rut = models.CharField(max_length=12, unique=True, verbose_name="RUT")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, verbose_name="Apellido")
    correo = models.EmailField(max_length=150, blank=True, null=True, verbose_name="Correo")
    delegacion = models.ForeignKey(Delegacion, on_delete=models.PROTECT, related_name='funcionarios')
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, verbose_name="Rol / Cargo")
    estado = models.BooleanField(default=True, verbose_name="Estado")

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.delegacion.nombre}"

# 4. Ítems y metas (Diseño 8 - Pág. 29)
class ItemMeta(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    estado = models.BooleanField(default=True, verbose_name="Estado")

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

# Modelo para Código de Recuperación de 3 pasos (Págs. 26 y 27)
class CodigoRecuperacion(models.Model):
    correo = models.EmailField()
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)
    intentos_fallidos = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.correo} - {self.codigo}"