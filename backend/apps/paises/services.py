import logging
import time

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

ETIQUETA_INDICADOR = {
    IndicadorEconomico.Tipo.PIB: 'PIB',
    IndicadorEconomico.Tipo.INFLACION: 'Inflacion',
    IndicadorEconomico.Tipo.DESEMPLEO: 'Desempleo',
    IndicadorEconomico.Tipo.BALANZA_COMERCIAL: 'Balanza comercial',
    IndicadorEconomico.Tipo.DEUDA_PIB: 'Deuda/PIB',
    IndicadorEconomico.Tipo.PIB_PERCAPITA: 'PIB per capita',
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

MAXIMO_REINTENTOS = 2
TIMEOUT_POR_INTENTO_SEGUNDOS = 20
# Techo propio por debajo del --timeout de gunicorn (120s), para que la sincronizacion
# completa nunca llegue a matar el worker aunque todos los indicadores necesiten reintentos.
PRESUPUESTO_SINCRONIZACION_SEGUNDOS = 100


def sincronizar_indicadores():
    inicio = time.monotonic()
    anio_actual = timezone.now().year
    desde = anio_actual - ANIOS_HISTORICO
    paises = {pais.codigo_iso: pais for pais in Pais.objects.filter(activo=True)}
    codigos_paises = ';'.join(paises.keys())

    paises_actualizados = set()
    indicadores_con_error = []
    errores = []

    logger.info('Inicio de sincronizacion de indicadores World Bank')

    for codigo_indicador, tipo in INDICADORES_WORLD_BANK.items():
        registros = None
        error_final = None

        for intento in range(MAXIMO_REINTENTOS + 1):
            presupuesto_restante = PRESUPUESTO_SINCRONIZACION_SEGUNDOS - (time.monotonic() - inicio)
            if presupuesto_restante <= 0:
                error_final = TimeoutError('se agoto el presupuesto de tiempo de la sincronizacion')
                break

            timeout_intento = min(TIMEOUT_POR_INTENTO_SEGUNDOS, presupuesto_restante)
            try:
                registros = _obtener_indicador_world_bank(codigos_paises, codigo_indicador, desde, anio_actual, timeout_intento)
                error_final = None
                break
            except Exception as exc:
                error_final = exc
                logger.warning(
                    'Intento %s/%s fallido para el indicador %s: %s',
                    intento + 1, MAXIMO_REINTENTOS + 1, codigo_indicador, exc,
                )

        if error_final is not None:
            logger.error('Error sincronizando el indicador %s: %s', codigo_indicador, error_final)
            indicadores_con_error.append(ETIQUETA_INDICADOR[tipo])
            errores.append({'indicador': ETIQUETA_INDICADOR[tipo], 'error': str(error_final)})
            continue

        paises_actualizados.update(_guardar_indicador(registros, paises, tipo))

    paises_procesados = sorted(paises_actualizados)

    logger.info(
        'Fin de sincronizacion de indicadores: %s paises actualizados, %s indicadores con error',
        len(paises_procesados), len(indicadores_con_error),
    )
    generar_alertas_sincronizacion(paises_procesados)
    return {
        'paises_procesados': paises_procesados,
        'indicadores_con_error': indicadores_con_error,
        'errores': errores,
    }


def _obtener_indicador_world_bank(codigos_paises, codigo_indicador, desde, hasta, timeout):
    """Una sola llamada para todos los paises (en vez de una por pais) para no
    superar el timeout del worker de gunicorn con decenas de llamadas secuenciales."""
    url = f'{settings.WORLDBANK_API_BASE_URL}/country/{codigos_paises}/indicator/{codigo_indicador}'
    respuesta = requests.get(
        url, params={'date': f'{desde}:{hasta}', 'format': 'json', 'per_page': 500}, timeout=timeout,
    )
    respuesta.raise_for_status()
    datos = respuesta.json()

    if len(datos) < 2 or not datos[1]:
        return []
    return datos[1]


def _guardar_indicador(registros, paises, tipo):
    """Guarda los valores recibidos y devuelve los codigos de los paises a los que
    se les actualizo al menos un dato (asi un pais cuenta como 'actualizado' aunque
    algun otro indicador haya fallado)."""
    paises_con_dato = set()

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
        paises_con_dato.add(pais.codigo_iso)

    return paises_con_dato


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
