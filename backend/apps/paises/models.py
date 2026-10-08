from django.db import models


class Pais(models.Model):
    class Region(models.TextChoices):
        ANDINA = 'ANDINA', 'Andina'
        CONO_SUR = 'CONO_SUR', 'Cono Sur'
        CENTROAMERICA = 'CENTROAMERICA', 'Centroamerica'
        CARIBE = 'CARIBE', 'Caribe'

    codigo_iso = models.CharField(max_length=2, primary_key=True)
    nombre = models.CharField(max_length=100)
    moneda_codigo = models.CharField(max_length=3, unique=True)
    moneda_nombre = models.CharField(max_length=100)
    region = models.CharField(max_length=20, choices=Region.choices)
    latitud = models.DecimalField(max_digits=9, decimal_places=4)
    longitud = models.DecimalField(max_digits=9, decimal_places=4)
    poblacion = models.PositiveBigIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']
        indexes = [models.Index(fields=['region'])]

    def __str__(self):
        return self.nombre


class IndicadorEconomico(models.Model):
    class Tipo(models.TextChoices):
        PIB = 'PIB', 'PIB'
        INFLACION = 'INFLACION', 'Inflacion'
        DESEMPLEO = 'DESEMPLEO', 'Desempleo'
        BALANZA_COMERCIAL = 'BALANZA_COMERCIAL', 'Balanza comercial'
        DEUDA_PIB = 'DEUDA_PIB', 'Deuda/PIB'
        PIB_PERCAPITA = 'PIB_PERCAPITA', 'PIB per capita'

    class Unidad(models.TextChoices):
        PORCENTAJE = 'PORCENTAJE', 'Porcentaje'
        USD = 'USD', 'USD'
        USD_MILES_MILLONES = 'USD_MILES_MILLONES', 'USD miles de millones'

    class Fuente(models.TextChoices):
        WORLD_BANK = 'WORLD_BANK', 'World Bank'
        MANUAL = 'MANUAL', 'Manual'

    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name='indicadores')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    valor = models.DecimalField(max_digits=14, decimal_places=4)
    unidad = models.CharField(max_length=20, choices=Unidad.choices)
    anio = models.PositiveIntegerField()
    fuente = models.CharField(max_length=10, choices=Fuente.choices)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['pais', 'tipo', 'anio'], name='unico_indicador_pais_tipo_anio'),
        ]
        indexes = [models.Index(fields=['pais', 'tipo', 'anio'])]
        ordering = ['-anio']

    def __str__(self):
        return f'{self.pais_id} {self.tipo} {self.anio}'


class TipoCambio(models.Model):
    class Fuente(models.TextChoices):
        EXCHANGERATE_API = 'EXCHANGERATE_API', 'ExchangeRate API'
        MANUAL = 'MANUAL', 'Manual'

    moneda_origen = models.ForeignKey(
        Pais, to_field='moneda_codigo', on_delete=models.CASCADE, related_name='tipos_cambio',
    )
    moneda_destino = models.CharField(max_length=3, default='USD')
    tasa = models.DecimalField(max_digits=14, decimal_places=6)
    fecha = models.DateField()
    variacion_porcentual = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    fuente = models.CharField(max_length=20, choices=Fuente.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['moneda_origen', 'fecha'], name='unico_tipocambio_origen_fecha'),
        ]
        indexes = [models.Index(fields=['moneda_origen', 'fecha'])]
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.moneda_origen_id} {self.fecha} {self.tasa}'
