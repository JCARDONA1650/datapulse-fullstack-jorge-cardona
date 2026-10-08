import statistics

from apps.alertas.services import evaluar_alerta_inflacion, evaluar_alertas_riesgo
from apps.paises.models import IndicadorEconomico, Pais

from .models import IndiceRiesgo

INDICADORES_EN_RIESGO_CANDIDATOS = [
    IndicadorEconomico.Tipo.INFLACION,
    IndicadorEconomico.Tipo.DESEMPLEO,
    IndicadorEconomico.Tipo.DEUDA_PIB,
]

COLOR_POR_NIVEL = {
    IndiceRiesgo.NivelRiesgo.BAJO: '#22c55e',
    IndiceRiesgo.NivelRiesgo.MODERADO: '#eab308',
    IndiceRiesgo.NivelRiesgo.ALTO: '#f97316',
    IndiceRiesgo.NivelRiesgo.CRITICO: '#ef4444',
}


def score_economico(pib_percapita, inflacion, desempleo, deuda_pib):
    penalizaciones = {}
    faltantes = []

    if pib_percapita is None:
        faltantes.append('PIB_PERCAPITA')
    elif pib_percapita < 3000:
        penalizaciones['PIB_PERCAPITA'] = -30
    elif pib_percapita < 6000:
        penalizaciones['PIB_PERCAPITA'] = -15
    elif pib_percapita < 12000:
        penalizaciones['PIB_PERCAPITA'] = -5

    if inflacion is None:
        faltantes.append('INFLACION')
    elif inflacion > 50:
        penalizaciones['INFLACION'] = -40
    elif inflacion > 10:
        penalizaciones['INFLACION'] = -25
    elif inflacion > 5:
        penalizaciones['INFLACION'] = -10

    if desempleo is None:
        faltantes.append('DESEMPLEO')
    elif desempleo > 15:
        penalizaciones['DESEMPLEO'] = -25
    elif desempleo > 10:
        penalizaciones['DESEMPLEO'] = -15
    elif desempleo > 7:
        penalizaciones['DESEMPLEO'] = -5

    if deuda_pib is None:
        faltantes.append('DEUDA_PIB')
    elif deuda_pib > 80:
        penalizaciones['DEUDA_PIB'] = -20
    elif deuda_pib > 50:
        penalizaciones['DEUDA_PIB'] = -10

    score = max(0, 100 + sum(penalizaciones.values()))
    return score, {'penalizaciones': penalizaciones, 'faltantes': faltantes}


def score_cambiario(volatilidad, depreciacion):
    penalizaciones = {}
    faltantes = []

    if volatilidad is None:
        faltantes.append('VOLATILIDAD')
    elif volatilidad > 3.0:
        penalizaciones['VOLATILIDAD'] = -40
    elif volatilidad > 1.5:
        penalizaciones['VOLATILIDAD'] = -25
    elif volatilidad > 0.5:
        penalizaciones['VOLATILIDAD'] = -10

    if depreciacion is None:
        faltantes.append('DEPRECIACION')
    elif depreciacion > 10:
        penalizaciones['DEPRECIACION'] = -30
    elif depreciacion > 5:
        penalizaciones['DEPRECIACION'] = -15
    elif depreciacion > 2:
        penalizaciones['DEPRECIACION'] = -5

    score = max(0, 100 + sum(penalizaciones.values()))
    return score, {'penalizaciones': penalizaciones, 'faltantes': faltantes}


def score_estabilidad(balanza_comercial, crecimiento_pib, indicadores_en_riesgo):
    penalizaciones = {}
    faltantes = []

    if balanza_comercial is None:
        faltantes.append('BALANZA_COMERCIAL')
    elif balanza_comercial < -10:
        penalizaciones['BALANZA_COMERCIAL'] = -25
    elif balanza_comercial < -5:
        penalizaciones['BALANZA_COMERCIAL'] = -15
    elif balanza_comercial < 0:
        penalizaciones['BALANZA_COMERCIAL'] = -5

    if crecimiento_pib is None:
        faltantes.append('CRECIMIENTO_PIB')
    elif crecimiento_pib < -2:
        penalizaciones['CRECIMIENTO_PIB'] = -30
    elif crecimiento_pib < 0:
        penalizaciones['CRECIMIENTO_PIB'] = -20
    elif crecimiento_pib < 1:
        penalizaciones['CRECIMIENTO_PIB'] = -10

    if indicadores_en_riesgo:
        penalizaciones['INDICADORES_EN_RIESGO'] = -5 * indicadores_en_riesgo

    score = max(0, 100 + sum(penalizaciones.values()))
    return score, {'penalizaciones': penalizaciones, 'faltantes': faltantes, 'indicadores_en_riesgo': indicadores_en_riesgo}


def contar_indicadores_en_riesgo(detalle_score_economico):
    penalizaciones = detalle_score_economico['penalizaciones']
    return sum(1 for tipo in INDICADORES_EN_RIESGO_CANDIDATOS if tipo in penalizaciones)


def calcular_volatilidad(tasas):
    cambios = [
        float((actual - anterior) / anterior * 100)
        for anterior, actual in zip(tasas[:-1], tasas[1:])
        if anterior
    ]
    if len(cambios) < 2:
        return None
    return statistics.stdev(cambios)


def calcular_depreciacion_acumulada(tasas):
    if len(tasas) < 2 or not tasas[0]:
        return None
    return float((tasas[-1] - tasas[0]) / tasas[0] * 100)


def calcular_crecimiento_pib(pib_actual, pib_anterior):
    if pib_actual is None or pib_anterior is None or not pib_anterior:
        return None
    return float((pib_actual - pib_anterior) / pib_anterior * 100)


def clasificar_nivel_riesgo(indice_compuesto):
    if indice_compuesto >= 75:
        return IndiceRiesgo.NivelRiesgo.BAJO
    if indice_compuesto >= 50:
        return IndiceRiesgo.NivelRiesgo.MODERADO
    if indice_compuesto >= 25:
        return IndiceRiesgo.NivelRiesgo.ALTO
    return IndiceRiesgo.NivelRiesgo.CRITICO


def _ultimo_valor(pais, tipo):
    indicador = pais.indicadores.filter(tipo=tipo).order_by('-anio').first()
    if not indicador:
        return None, None
    return float(indicador.valor), indicador.anio


def _pib_anio_anterior(pais, anio_actual):
    if anio_actual is None:
        return None
    indicador = pais.indicadores.filter(
        tipo=IndicadorEconomico.Tipo.PIB, anio__lt=anio_actual,
    ).order_by('-anio').first()
    return float(indicador.valor) if indicador else None


def _tasas_ultimos_30_dias(pais):
    registros = list(pais.tipos_cambio.order_by('-fecha')[:30])
    registros.reverse()
    return [float(registro.tasa) for registro in registros]


def calcular_irpc_pais(pais):
    pib_percapita, anio_pib_percapita = _ultimo_valor(pais, IndicadorEconomico.Tipo.PIB_PERCAPITA)
    inflacion, anio_inflacion = _ultimo_valor(pais, IndicadorEconomico.Tipo.INFLACION)
    desempleo, anio_desempleo = _ultimo_valor(pais, IndicadorEconomico.Tipo.DESEMPLEO)
    deuda_pib, anio_deuda = _ultimo_valor(pais, IndicadorEconomico.Tipo.DEUDA_PIB)
    balanza, anio_balanza = _ultimo_valor(pais, IndicadorEconomico.Tipo.BALANZA_COMERCIAL)
    pib_actual, anio_pib = _ultimo_valor(pais, IndicadorEconomico.Tipo.PIB)
    pib_anterior = _pib_anio_anterior(pais, anio_pib)

    economico, detalle_economico = score_economico(pib_percapita, inflacion, desempleo, deuda_pib)

    es_dolarizado = pais.moneda_codigo == 'USD'
    if es_dolarizado:
        cambiario = 100
        detalle_cambiario = {'penalizaciones': {}, 'faltantes': [], 'nota': 'Pais dolarizado, score fijo en 100'}
        volatilidad = depreciacion = None
    else:
        tasas = _tasas_ultimos_30_dias(pais)
        volatilidad = calcular_volatilidad(tasas)
        depreciacion = calcular_depreciacion_acumulada(tasas)
        cambiario, detalle_cambiario = score_cambiario(volatilidad, depreciacion)

    indicadores_en_riesgo = contar_indicadores_en_riesgo(detalle_economico)
    crecimiento = calcular_crecimiento_pib(pib_actual, pib_anterior)
    estabilidad, detalle_estabilidad = score_estabilidad(balanza, crecimiento, indicadores_en_riesgo)

    indice_compuesto = round(economico * 0.40 + cambiario * 0.30 + estabilidad * 0.30, 2)
    nivel_riesgo = clasificar_nivel_riesgo(indice_compuesto)

    detalle_calculo = {
        'anios_usados': {
            'PIB_PERCAPITA': anio_pib_percapita, 'INFLACION': anio_inflacion, 'DESEMPLEO': anio_desempleo,
            'DEUDA_PIB': anio_deuda, 'BALANZA_COMERCIAL': anio_balanza, 'PIB': anio_pib,
        },
        'score_economico': detalle_economico,
        'score_cambiario': detalle_cambiario,
        'score_estabilidad': detalle_estabilidad,
        'volatilidad': volatilidad,
        'depreciacion_acumulada': depreciacion,
        'crecimiento_pib': crecimiento,
    }

    indice_anterior = IndiceRiesgo.objects.filter(pais=pais).order_by('-fecha_calculo').first()

    indice_actual = IndiceRiesgo.objects.create(
        pais=pais,
        score_economico=economico,
        score_cambiario=cambiario,
        score_estabilidad=estabilidad,
        indice_compuesto=indice_compuesto,
        nivel_riesgo=nivel_riesgo,
        detalle_calculo=detalle_calculo,
    )

    evaluar_alertas_riesgo(indice_actual, indice_anterior)
    evaluar_alerta_inflacion(pais, inflacion)

    return indice_actual


def calcular_irpc_todos():
    resultados = [calcular_irpc_pais(pais) for pais in Pais.objects.filter(activo=True)]
    return resultados
