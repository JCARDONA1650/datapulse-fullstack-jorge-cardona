from django.conf import settings
from django.core.validators import MaxValueValidator, MinLengthValidator, MinValueValidator
from django.db import models

from apps.paises.models import Pais


class Portafolio(models.Model):
    nombre = models.CharField(max_length=100, validators=[MinLengthValidator(3)])
    descripcion = models.CharField(max_length=500, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portafolios')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    es_publico = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'nombre'], condition=models.Q(activo=True), name='unico_nombre_portafolio_activo',
            ),
        ]
        indexes = [models.Index(fields=['usuario', 'activo'])]
        ordering = ['-fecha_modificacion']

    def __str__(self):
        return self.nombre


class Posicion(models.Model):
    class TipoActivo(models.TextChoices):
        RENTA_FIJA = 'RENTA_FIJA', 'Renta fija'
        RENTA_VARIABLE = 'RENTA_VARIABLE', 'Renta variable'
        COMMODITIES = 'COMMODITIES', 'Commodities'
        MONEDA = 'MONEDA', 'Moneda'

    portafolio = models.ForeignKey(Portafolio, on_delete=models.CASCADE, related_name='posiciones')
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='posiciones')
    tipo_activo = models.CharField(max_length=20, choices=TipoActivo.choices)
    monto_inversion_usd = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(1000), MaxValueValidator(10_000_000)],
    )
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField(null=True, blank=True)
    notas = models.CharField(max_length=200, blank=True)

    class Meta:
        indexes = [models.Index(fields=['portafolio', 'fecha_salida'])]
        ordering = ['-fecha_entrada']

    def __str__(self):
        return f'{self.portafolio_id} - {self.pais_id} - {self.tipo_activo}'
