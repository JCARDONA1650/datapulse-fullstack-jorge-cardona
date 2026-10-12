import random
from datetime import timedelta

from django.utils import timezone

from .models import IndicadorEconomico, Pais, TipoCambio

# Poblacion y cifras economicas son valores aproximados/ilustrativos para la demo,
# no proceden de una fuente oficial (igual que el caso de prueba de Colombia en HU_GLOBAL).

PAISES = [
    {'codigo_iso': 'CO', 'nombre': 'Colombia', 'moneda_codigo': 'COP', 'moneda_nombre': 'Peso colombiano', 'region': Pais.Region.ANDINA, 'latitud': 4.5709, 'longitud': -74.2973, 'poblacion': 52_000_000},
    {'codigo_iso': 'BR', 'nombre': 'Brasil', 'moneda_codigo': 'BRL', 'moneda_nombre': 'Real brasileno', 'region': Pais.Region.CONO_SUR, 'latitud': -14.2350, 'longitud': -51.9253, 'poblacion': 216_000_000},
    {'codigo_iso': 'MX', 'nombre': 'Mexico', 'moneda_codigo': 'MXN', 'moneda_nombre': 'Peso mexicano', 'region': Pais.Region.CENTROAMERICA, 'latitud': 23.6345, 'longitud': -102.5528, 'poblacion': 128_000_000},
    {'codigo_iso': 'AR', 'nombre': 'Argentina', 'moneda_codigo': 'ARS', 'moneda_nombre': 'Peso argentino', 'region': Pais.Region.CONO_SUR, 'latitud': -38.4161, 'longitud': -63.6167, 'poblacion': 46_000_000},
    {'codigo_iso': 'CL', 'nombre': 'Chile', 'moneda_codigo': 'CLP', 'moneda_nombre': 'Peso chileno', 'region': Pais.Region.CONO_SUR, 'latitud': -35.6751, 'longitud': -71.5430, 'poblacion': 19_500_000},
    {'codigo_iso': 'PE', 'nombre': 'Peru', 'moneda_codigo': 'PEN', 'moneda_nombre': 'Sol peruano', 'region': Pais.Region.ANDINA, 'latitud': -9.1900, 'longitud': -75.0152, 'poblacion': 34_000_000},
    {'codigo_iso': 'EC', 'nombre': 'Ecuador', 'moneda_codigo': 'USD', 'moneda_nombre': 'Dolar estadounidense', 'region': Pais.Region.ANDINA, 'latitud': -1.8312, 'longitud': -78.1834, 'poblacion': 18_000_000},
    {'codigo_iso': 'UY', 'nombre': 'Uruguay', 'moneda_codigo': 'UYU', 'moneda_nombre': 'Peso uruguayo', 'region': Pais.Region.CONO_SUR, 'latitud': -32.5228, 'longitud': -55.7658, 'poblacion': 3_500_000},
    {'codigo_iso': 'PY', 'nombre': 'Paraguay', 'moneda_codigo': 'PYG', 'moneda_nombre': 'Guarani paraguayo', 'region': Pais.Region.CONO_SUR, 'latitud': -23.4425, 'longitud': -58.4438, 'poblacion': 6_800_000},
    {'codigo_iso': 'PA', 'nombre': 'Panama', 'moneda_codigo': 'PAB', 'moneda_nombre': 'Balboa panameno', 'region': Pais.Region.CENTROAMERICA, 'latitud': 8.5380, 'longitud': -80.7821, 'poblacion': 4_400_000},
]

# anio -> pib (miles de millones USD), pib_percapita (USD), inflacion (%), desempleo (%), balanza (% PIB), deuda_pib (% PIB)
# El ultimo anio de CO reproduce el caso de prueba obligatorio de HU_GLOBAL seccion 4.
INDICADORES = {
    'CO': [
        (2021, 330.00, 6500, 8.0, 12.0, -3.5, 58),
        (2022, 350.00, 6650, 10.5, 11.8, -4.0, 56),
        (2023, 355.25, 6800, 9.2, 11.3, -4.2, 55),
    ],
    'BR': [
        (2021, 1600, 7400, 8.3, 13.2, -1.0, 85),
        (2022, 1850, 8200, 9.3, 9.3, -0.5, 84),
        (2023, 2100, 9100, 4.6, 7.9, 1.2, 85),
    ],
    'MX': [
        (2021, 1300, 9900, 5.7, 4.4, 0.5, 52),
        (2022, 1420, 10800, 7.9, 3.6, 0.2, 50),
        (2023, 1550, 11600, 4.7, 2.8, 0.8, 48),
    ],
    'AR': [
        (2021, 490, 10600, 48.4, 8.7, 1.6, 80),
        (2022, 630, 13700, 72.4, 6.9, -0.4, 85),
        (2023, 640, 13700, 211.0, 5.7, -1.0, 90),
    ],
    'CL': [
        (2021, 317, 16300, 4.5, 8.9, -1.5, 36),
        (2022, 301, 15300, 11.6, 7.9, -6.5, 38),
        (2023, 335, 16700, 3.9, 8.6, 1.0, 40),
    ],
    'PE': [
        (2021, 223, 6600, 4.0, 5.7, -1.5, 36),
        (2022, 242, 7100, 8.0, 4.8, -3.0, 34),
        (2023, 267, 7790, 3.2, 4.3, -1.0, 33),
    ],
    'EC': [
        (2021, 106, 6100, 0.1, 5.7, 1.5, 57),
        (2022, 115, 6600, 3.5, 3.5, 2.0, 55),
        (2023, 118, 6700, 2.2, 3.8, 1.0, 54),
    ],
    'UY': [
        (2021, 61, 17400, 7.7, 9.3, 1.0, 61),
        (2022, 71, 20100, 9.1, 7.9, 0.5, 60),
        (2023, 76, 21300, 5.1, 8.0, 1.5, 58),
    ],
    'PY': [
        (2021, 39, 5400, 4.8, 6.9, -2.0, 32),
        (2022, 41, 5600, 9.8, 6.6, -4.0, 36),
        (2023, 44, 5900, 3.4, 6.1, -1.0, 35),
    ],
    'PA': [
        (2021, 63, 14500, 1.6, 11.3, -5.0, 57),
        (2022, 76, 17300, 2.9, 8.6, -6.0, 55),
        (2023, 82, 18600, 1.5, 7.4, -3.0, 54),
    ],
}

TASAS_BASE = {'COP': 4800, 'BRL': 5.4, 'MXN': 18.5, 'ARS': 980, 'CLP': 950, 'PEN': 3.75, 'UYU': 41, 'PYG': 7300, 'PAB': 1.0}
VOLATILIDAD_DIARIA = {'COP': 0.5, 'BRL': 0.6, 'MXN': 0.4, 'ARS': 1.8, 'CLP': 0.5, 'PEN': 0.3, 'UYU': 0.3, 'PYG': 0.3, 'PAB': 0.0}

DIAS_HISTORICO = 30


def crear_paises():
    for datos in PAISES:
        Pais.objects.get_or_create(codigo_iso=datos['codigo_iso'], defaults={k: v for k, v in datos.items() if k != 'codigo_iso'})


def crear_indicadores():
    tipos_por_posicion = [
        IndicadorEconomico.Tipo.PIB,
        IndicadorEconomico.Tipo.PIB_PERCAPITA,
        IndicadorEconomico.Tipo.INFLACION,
        IndicadorEconomico.Tipo.DESEMPLEO,
        IndicadorEconomico.Tipo.BALANZA_COMERCIAL,
        IndicadorEconomico.Tipo.DEUDA_PIB,
    ]
    unidades_por_tipo = {
        IndicadorEconomico.Tipo.PIB: IndicadorEconomico.Unidad.USD_MILES_MILLONES,
        IndicadorEconomico.Tipo.PIB_PERCAPITA: IndicadorEconomico.Unidad.USD,
        IndicadorEconomico.Tipo.INFLACION: IndicadorEconomico.Unidad.PORCENTAJE,
        IndicadorEconomico.Tipo.DESEMPLEO: IndicadorEconomico.Unidad.PORCENTAJE,
        IndicadorEconomico.Tipo.BALANZA_COMERCIAL: IndicadorEconomico.Unidad.PORCENTAJE,
        IndicadorEconomico.Tipo.DEUDA_PIB: IndicadorEconomico.Unidad.PORCENTAJE,
    }

    for codigo_iso, anios in INDICADORES.items():
        pais = Pais.objects.get(codigo_iso=codigo_iso)
        for fila in anios:
            anio = fila[0]
            for tipo, valor in zip(tipos_por_posicion, fila[1:]):
                IndicadorEconomico.objects.update_or_create(
                    pais=pais, tipo=tipo, anio=anio,
                    defaults={'valor': valor, 'unidad': unidades_por_tipo[tipo], 'fuente': IndicadorEconomico.Fuente.MANUAL},
                )


def crear_tipos_cambio():
    aleatorio = random.Random(42)
    hoy = timezone.now().date()

    for moneda_codigo, base in TASAS_BASE.items():
        pais = Pais.objects.get(moneda_codigo=moneda_codigo)
        sigma = VOLATILIDAD_DIARIA[moneda_codigo]
        tasa_anterior = None

        for i in range(DIAS_HISTORICO):
            fecha = hoy - timedelta(days=DIAS_HISTORICO - 1 - i)
            if sigma == 0:
                tasa = base
            else:
                variacion_pct = aleatorio.gauss(0, sigma)
                tasa = base if tasa_anterior is None else tasa_anterior * (1 + variacion_pct / 100)

            variacion = None
            if tasa_anterior:
                variacion = (tasa - tasa_anterior) / tasa_anterior * 100

            TipoCambio.objects.update_or_create(
                moneda_origen=pais, fecha=fecha,
                defaults={
                    'moneda_destino': 'USD', 'tasa': round(tasa, 6),
                    'variacion_porcentual': round(variacion, 4) if variacion is not None else None,
                    'fuente': TipoCambio.Fuente.MANUAL,
                },
            )
            tasa_anterior = tasa
