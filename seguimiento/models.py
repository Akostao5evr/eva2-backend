from django.db import models
from gestion.models import Delegacion, Funcionario

# Create your models here.

class Actividad(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Validación'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    
    codigo_verificador = models.CharField(max_length=20, unique=True)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    delegacion = models.ForeignKey(Delegacion, on_delete=models.CASCADE)
    descripcion = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    def __str__(self):
        return f"{self.codigo_verificador} - {self.funcionario.nombre}"

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