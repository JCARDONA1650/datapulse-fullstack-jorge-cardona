from apps.paises.models import Pais

from .models import Alerta

CAIDA_IRPC_ALERTA = 15
VARIACION_TIPO_CAMBIO_ALERTA = 3
INFLACION_HIPERINFLACION = 50
IRPC_CRITICO = 25


def generar_alerta(pais, tipo_alerta, severidad, titulo, mensaje, usuario=None):
    return Alerta.objects.create(
        usuario=usuario, pais=pais, tipo_alerta=tipo_alerta, severidad=severidad, titulo=titulo, mensaje=mensaje,
    )


def _ya_hay_alerta_sin_leer(pais, tipo_alerta, titulo):
    """Evita reabrir la misma alerta en cada recalculo mientras la condicion no cambie y nadie la haya leido."""
    return Alerta.objects.filter(pais=pais, tipo_alerta=tipo_alerta, titulo=titulo, leida=False).exists()


def evaluar_alertas_riesgo(indice_actual, indice_anterior):
    pais = indice_actual.pais

    if indice_actual.indice_compuesto < IRPC_CRITICO:
        titulo = f'Riesgo critico en {pais.nombre}'
        if not _ya_hay_alerta_sin_leer(pais, Alerta.TipoAlerta.RIESGO, titulo):
            generar_alerta(
                pais, Alerta.TipoAlerta.RIESGO, Alerta.Severidad.CRITICAL, titulo,
                f'El IRPC de {pais.nombre} es {indice_actual.indice_compuesto}, por debajo del umbral critico ({IRPC_CRITICO}).',
            )

    if indice_anterior is not None:
        caida = float(indice_anterior.indice_compuesto) - float(indice_actual.indice_compuesto)
        if caida > CAIDA_IRPC_ALERTA:
            generar_alerta(
                pais, Alerta.TipoAlerta.RIESGO, Alerta.Severidad.WARNING,
                f'Caida fuerte del IRPC en {pais.nombre}',
                f'El IRPC de {pais.nombre} cayo {caida:.2f} puntos respecto al calculo anterior '
                f'({indice_anterior.indice_compuesto} -> {indice_actual.indice_compuesto}).',
            )


def evaluar_alerta_inflacion(pais, inflacion):
    if inflacion is not None and inflacion > INFLACION_HIPERINFLACION:
        titulo = f'Hiperinflacion en {pais.nombre}'
        if not _ya_hay_alerta_sin_leer(pais, Alerta.TipoAlerta.INDICADOR, titulo):
            generar_alerta(
                pais, Alerta.TipoAlerta.INDICADOR, Alerta.Severidad.CRITICAL, titulo,
                f'La inflacion de {pais.nombre} es {inflacion}%, supera el umbral de hiperinflacion ({INFLACION_HIPERINFLACION}%).',
            )


def evaluar_alerta_tipo_cambio(tipo_cambio):
    variacion = tipo_cambio.variacion_porcentual
    if variacion is not None and abs(variacion) > VARIACION_TIPO_CAMBIO_ALERTA:
        pais = tipo_cambio.moneda_origen
        titulo = f'Variacion fuerte del tipo de cambio en {pais.nombre} ({tipo_cambio.fecha})'
        if not _ya_hay_alerta_sin_leer(pais, Alerta.TipoAlerta.TIPO_CAMBIO, titulo):
            generar_alerta(
                pais, Alerta.TipoAlerta.TIPO_CAMBIO, Alerta.Severidad.WARNING, titulo,
                f'La tasa {pais.moneda_codigo}/USD vario {variacion:.2f}% en un dia ({tipo_cambio.fecha}).',
            )


def generar_alertas_sincronizacion(codigos_paises_procesados):
    """
    Alerta.pais es obligatorio (no nullable), asi que en vez de una sola alerta
    global para todo el lote, se genera una alerta INFO por cada pais con datos nuevos.
    """
    alertas = []
    for pais in Pais.objects.filter(codigo_iso__in=codigos_paises_procesados):
        alertas.append(generar_alerta(
            pais, Alerta.TipoAlerta.INDICADOR, Alerta.Severidad.INFO,
            f'Nuevos datos economicos para {pais.nombre}',
            f'Se sincronizaron los indicadores economicos de {pais.nombre} desde World Bank.',
        ))
    return alertas
