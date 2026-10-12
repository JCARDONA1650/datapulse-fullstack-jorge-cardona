import logging

import requests
from django.conf import settings
from django.utils import timezone

from apps.alertas.services import evaluar_alerta_tipo_cambio, generar_alertas_sincronizacion

from .models import IndicadorEconomico, Pais, TipoCambio

logger = logging.getLogger(__name__)

INDICADORES_WORLD_BANK = {
    'NY.GDP.MKTP.CD': IndicadorEconomico.Tipo.PIB,
    'FP.CPI.TOTL.ZG': IndicadorEconomico.Tipo.INFLACION,
    'SL.UEM.TOTL.ZS': IndicadorEconomico.Tipo.DESEMPLEO,
    'NE.RSB.GNFS.ZS': IndicadorEconomico.Tipo.BALANZA_COMERCIAL,
    'GC.DOD.TOTL.GD.ZS': IndicadorEconomico.Tipo.DEUDA_PIB,
    'NY.GDP.PCAP.CD': IndicadorEconomico.Tipo.PIB_PERCAPITA,
}

UNIDAD_POR_TIPO = {
    IndicadorEconomico.Tipo.PIB: IndicadorEconomico.Unidad.USD_MILES_MILLONES,
    IndicadorEconomico.Tipo.INFLACION: IndicadorEconomico.Unidad.PORCENTAJE,
    IndicadorEconomico.Tipo.DESEMPLEO: IndicadorEconomico.Unidad.PORCENTAJE,
    IndicadorEconomico.Tipo.BALANZA_COMERCIAL: IndicadorEconomico.Unidad.PORCENTAJE,
    IndicadorEconomico.Tipo.DEUDA_PIB: IndicadorEconomico.Unidad.PORCENTAJE,
    IndicadorEconomico.Tipo.PIB_PERCAPITA: IndicadorEconomico.Unidad.USD,
}

ANIOS_HISTORICO = 5
TASA_FIJA_RESPALDO = {'PAB': 1.0}


def sincronizar_indicadores():
    anio_actual = timezone.now().year
    desde = anio_actual - ANIOS_HISTORICO
    paises_procesados = []
    errores = []

    logger.info('Inicio de sincronizacion de indicadores World Bank')

    for pais in Pais.objects.filter(activo=True):
        try:
            _sincronizar_indicadores_pais(pais, desde, anio_actual)
            paises_procesados.append(pais.codigo_iso)
        except Exception as exc:
            logger.error('Error sincronizando indicadores de %s: %s', pais.codigo_iso, exc)
            errores.append({'pais': pais.codigo_iso, 'error': str(exc)})

    logger.info(
        'Fin de sincronizacion de indicadores: %s paises ok, %s errores',
        len(paises_procesados), len(errores),
    )
    generar_alertas_sincronizacion(paises_procesados)
    return {'paises_procesados': paises_procesados, 'errores': errores}


def _sincronizar_indicadores_pais(pais, desde, hasta):
    for codigo_indicador, tipo in INDICADORES_WORLD_BANK.items():
        url = f'{settings.WORLDBANK_API_BASE_URL}/country/{pais.codigo_iso}/indicator/{codigo_indicador}'
        respuesta = requests.get(
            url, params={'date': f'{desde}:{hasta}', 'format': 'json', 'per_page': 100}, timeout=10,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()

        if len(datos) < 2 or not datos[1]:
            continue

        for registro in datos[1]:
            if registro['value'] is None:
                continue

            valor = registro['value']
            if tipo == IndicadorEconomico.Tipo.PIB:
                valor = valor / 1_000_000_000

            IndicadorEconomico.objects.update_or_create(
                pais=pais,
                tipo=tipo,
                anio=int(registro['date']),
                defaults={
                    'valor': valor,
                    'unidad': UNIDAD_POR_TIPO[tipo],
                    'fuente': IndicadorEconomico.Fuente.WORLD_BANK,
                },
            )


def sincronizar_tipos_cambio():
    logger.info('Inicio de sincronizacion de tipos de cambio')

    url = f'{settings.EXCHANGERATE_API_BASE_URL}/latest/USD'
    respuesta = requests.get(url, timeout=10)
    respuesta.raise_for_status()
    tasas = respuesta.json().get('rates', {})
    fecha = timezone.now().date()

    paises_procesados = []
    errores = []

    for pais in Pais.objects.filter(activo=True).exclude(moneda_codigo='USD'):
        try:
            tasa = tasas.get(pais.moneda_codigo, TASA_FIJA_RESPALDO.get(pais.moneda_codigo))
            if tasa is None:
                raise ValueError(f'No se encontro tasa para {pais.moneda_codigo}')

            anterior = TipoCambio.objects.filter(moneda_origen=pais).order_by('-fecha').first()
            variacion = None
            if anterior and anterior.tasa:
                variacion = (tasa - float(anterior.tasa)) / float(anterior.tasa) * 100

            tipo_cambio, _ = TipoCambio.objects.update_or_create(
                moneda_origen=pais,
                fecha=fecha,
                defaults={
                    'moneda_destino': 'USD',
                    'tasa': tasa,
                    'variacion_porcentual': variacion,
                    'fuente': TipoCambio.Fuente.EXCHANGERATE_API,
                },
            )
            evaluar_alerta_tipo_cambio(tipo_cambio)
            paises_procesados.append(pais.codigo_iso)
        except Exception as exc:
            logger.error('Error sincronizando tipo de cambio de %s: %s', pais.codigo_iso, exc)
            errores.append({'pais': pais.codigo_iso, 'error': str(exc)})

    logger.info(
        'Fin de sincronizacion de tipos de cambio: %s ok, %s errores',
        len(paises_procesados), len(errores),
    )
    return {'paises_procesados': paises_procesados, 'errores': errores}
