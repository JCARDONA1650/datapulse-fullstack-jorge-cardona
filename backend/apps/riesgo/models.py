from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.paises.models import Pais


class IndiceRiesgo(models.Model):
    class NivelRiesgo(models.TextChoices):
        BAJO = 'BAJO', 'Bajo'
        MODERADO = 'MODERADO', 'Moderado'
        ALTO = 'ALTO', 'Alto'
        CRITICO = 'CRITICO', 'Critico'

    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='indices_riesgo')
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    score_economico = models.DecimalField(max_digits=5, decimal_places=2)
    score_cambiario = models.DecimalField(max_digits=5, decimal_places=2)
    score_estabilidad = models.DecimalField(max_digits=5, decimal_places=2)
    indice_compuesto = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    nivel_riesgo = models.CharField(max_length=10, choices=NivelRiesgo.choices)
    detalle_calculo = models.JSONField(default=dict)

    class Meta:
        indexes = [models.Index(fields=['pais', 'fecha_calculo'])]
        ordering = ['-fecha_calculo']

    def __str__(self):
        return f'{self.pais_id} {self.fecha_calculo:%Y-%m-%d} {self.indice_compuesto}'
