from django.db import models
from django.contrib.auth.models import User
from gestion.models import Delegacion, Funcionario

# 5. Tipo de Atención (Diseño 9 - Pág. 30)
class TipoAtencion(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    estado = models.BooleanField(default=True, verbose_name="Estado")

    def __str__(self):
        return self.nombre

# 6. Sub Atención (Diseño 10 - Pág. 30)
class SubAtencion(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    tipo_atencion = models.ForeignKey(TipoAtencion, on_delete=models.CASCADE, related_name='subatenciones', verbose_name="Tipo asociado")
    estado = models.BooleanField(default=True, verbose_name="Estado")

    def __str__(self):
        return f"{self.nombre} ({self.tipo_atencion.nombre})"

# Ingreso de Atención Ciudadana / Actividad (Diseño 11 - Pág. 31)
class Actividad(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Validación'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    
    codigo_verificador = models.CharField(max_length=20, unique=True)
    solicitante = models.CharField(max_length=150, default="Vecino no especificado", verbose_name="Vecino o solicitante")
    tipo_atencion = models.ForeignKey(TipoAtencion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Tipo de Atención")
    sub_atencion = models.ForeignKey(SubAtencion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Sub Atención")
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, verbose_name="Responsable")
    delegacion = models.ForeignKey(Delegacion, on_delete=models.CASCADE, verbose_name="Delegación")
    descripcion = models.TextField(verbose_name="Descripción de la atención")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    def __str__(self):
        return f"{self.codigo_verificador} - {self.solicitante}"

class Evidencia(models.Model):
    actividad = models.OneToOneField(Actividad, on_delete=models.CASCADE, related_name='evidencia')
    foto_antes = models.ImageField(upload_to='evidencias/antes/', blank=True, null=True)
    foto_despues = models.ImageField(upload_to='evidencias/despues/', blank=True, null=True)
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Evidencia de {self.actividad.codigo_verificador}"

class CompromisoTicket(models.Model):
    SEMAFORO = [
        ('BLANCO', 'Reciente'),
        ('VERDE', 'A tiempo'),
        ('AMARILLO', 'Próximo a vencer'),
        ('ROJO', 'Vencido'),
    ]

    solicitante = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    delegacion = models.ForeignKey(Delegacion, on_delete=models.CASCADE)
    funcionario_asignado = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    fecha_limite = models.DateField()
    estado_color = models.CharField(max_length=10, choices=SEMAFORO, default='BLANCO')

    def __str__(self):
        return f"Ticket {self.id} - {self.sector} ({self.estado_color})"