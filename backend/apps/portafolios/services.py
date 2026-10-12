from datetime import date

from django.core.exceptions import ValidationError
from django.db.models import Q, Sum

from .models import Posicion

MONTO_MAXIMO_PORTAFOLIO = 50_000_000
MAXIMO_POSICIONES_ACTIVAS_MISMO_TIPO_PAIS = 2


def validar_posicion(portafolio, pais, tipo_activo, monto_inversion_usd, fecha_entrada, fecha_salida, posicion_actual=None):
    errores = {}

    if fecha_salida and fecha_entrada and fecha_salida <= fecha_entrada:
        errores['fecha_salida'] = 'La fecha de salida debe ser posterior a la fecha de entrada.'

    if fecha_entrada and fecha_entrada > date.today():
        errores['fecha_entrada'] = 'La fecha de entrada no puede ser futura.'

    if tipo_activo == Posicion.TipoActivo.MONEDA and pais.moneda_codigo == 'USD':
        errores['tipo_activo'] = f'No se permite una posicion de tipo MONEDA para {pais.nombre}, cuya moneda es USD.'

    activas = portafolio.posiciones.filter(fecha_salida__isnull=True)
    if posicion_actual is not None:
        activas = activas.exclude(pk=posicion_actual.pk)

    monto_actual_total = activas.aggregate(total=Sum('monto_inversion_usd'))['total'] or 0
    if not fecha_salida and (monto_actual_total + monto_inversion_usd) > MONTO_MAXIMO_PORTAFOLIO:
        errores['monto_inversion_usd'] = (
            f'El monto total del portafolio no puede superar {MONTO_MAXIMO_PORTAFOLIO:,.0f} USD.'
        )

    mismo_tipo_pais = activas.filter(tipo_activo=tipo_activo, pais=pais).count()
    if not fecha_salida and mismo_tipo_pais >= MAXIMO_POSICIONES_ACTIVAS_MISMO_TIPO_PAIS:
        errores['tipo_activo'] = (
            f'Ya existen {MAXIMO_POSICIONES_ACTIVAS_MISMO_TIPO_PAIS} posiciones activas de tipo {tipo_activo} '
            f'en {pais.nombre} para este portafolio.'
        )

    if errores:
        raise ValidationError(errores)


def calcular_resumen_portafolio(portafolio):
    posiciones = portafolio.posiciones.filter(fecha_salida__isnull=True).select_related('pais')
    monto_total = posiciones.aggregate(total=Sum('monto_inversion_usd'))['total'] or 0

    por_pais = {}
    por_tipo_activo = {}
    for posicion in posiciones:
        por_pais[posicion.pais_id] = por_pais.get(posicion.pais_id, 0) + float(posicion.monto_inversion_usd)
        por_tipo_activo[posicion.tipo_activo] = por_tipo_activo.get(posicion.tipo_activo, 0) + float(posicion.monto_inversion_usd)

    riesgo_promedio_ponderado = _riesgo_promedio_ponderado(posiciones, float(monto_total))

    return {
        'monto_total_usd': float(monto_total),
        'distribucion_por_pais': por_pais,
        'distribucion_por_tipo_activo': por_tipo_activo,
        'riesgo_promedio_ponderado': riesgo_promedio_ponderado,
    }


def _riesgo_promedio_ponderado(posiciones, monto_total):
    if not monto_total:
        return None

    acumulado = 0.0
    for posicion in posiciones:
        indice = posicion.pais.indices_riesgo.order_by('-fecha_calculo').first()
        if indice:
            peso = float(posicion.monto_inversion_usd) / monto_total
            acumulado += peso * float(indice.indice_compuesto)

    return round(acumulado, 2) if acumulado else None
