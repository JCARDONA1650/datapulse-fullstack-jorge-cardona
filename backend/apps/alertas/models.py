from django.conf import settings
from django.db import models

from apps.paises.models import Pais


class Alerta(models.Model):
    class TipoAlerta(models.TextChoices):
        RIESGO = 'RIESGO', 'Riesgo'
        TIPO_CAMBIO = 'TIPO_CAMBIO', 'Tipo de cambio'
        INDICADOR = 'INDICADOR', 'Indicador'

    class Severidad(models.TextChoices):
        INFO = 'INFO', 'Info'
        WARNING = 'WARNING', 'Warning'
        CRITICAL = 'CRITICAL', 'Critical'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alertas', null=True, blank=True,
    )
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='alertas')
    tipo_alerta = models.CharField(max_length=15, choices=TipoAlerta.choices)
    severidad = models.CharField(max_length=10, choices=Severidad.choices)
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['usuario', 'leida']),
            models.Index(fields=['pais', 'fecha_creacion']),
        ]
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.severidad} - {self.titulo}'
