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
    paises = {pais.codigo_iso: pais for pais in Pais.objects.filter(activo=True)}
    codigos_paises = ';'.join(paises.keys())

    paises_con_error = set()
    errores = []

    logger.info('Inicio de sincronizacion de indicadores World Bank')

    for codigo_indicador, tipo in INDICADORES_WORLD_BANK.items():
        try:
            registros = _obtener_indicador_world_bank(codigos_paises, codigo_indicador, desde, anio_actual)
        except Exception as exc:
            logger.error('Error sincronizando el indicador %s: %s', codigo_indicador, exc)
            for codigo_iso in paises:
                paises_con_error.add(codigo_iso)
                errores.append({'pais': codigo_iso, 'error': f'{codigo_indicador}: {exc}'})
            continue

        _guardar_indicador(registros, paises, tipo)

    paises_procesados = [codigo_iso for codigo_iso in paises if codigo_iso not in paises_con_error]

    logger.info(
        'Fin de sincronizacion de indicadores: %s paises ok, %s errores',
        len(paises_procesados), len(errores),
    )
    generar_alertas_sincronizacion(paises_procesados)
    return {'paises_procesados': paises_procesados, 'errores': errores}


def _obtener_indicador_world_bank(codigos_paises, codigo_indicador, desde, hasta):
    """Una sola llamada para todos los paises (en vez de una por pais) para no
    superar el timeout del worker de gunicorn con decenas de llamadas secuenciales."""
    url = f'{settings.WORLDBANK_API_BASE_URL}/country/{codigos_paises}/indicator/{codigo_indicador}'
    respuesta = requests.get(
        url, params={'date': f'{desde}:{hasta}', 'format': 'json', 'per_page': 500}, timeout=10,
    )
    respuesta.raise_for_status()
    datos = respuesta.json()

    if len(datos) < 2 or not datos[1]:
        return []
    return datos[1]


def _guardar_indicador(registros, paises, tipo):
    for registro in registros:
        if registro['value'] is None:
            continue

        pais = paises.get(registro.get('country', {}).get('id'))
        if pais is None:
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
