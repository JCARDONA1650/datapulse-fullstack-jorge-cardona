from rest_framework import serializers


class ResumenDashboardSerializer(serializers.Serializer):
    total_paises_monitoreados = serializers.IntegerField()
    alertas_activas = serializers.IntegerField()
    portafolios_usuario = serializers.IntegerField()
    promedio_irpc_region = serializers.FloatField(allow_null=True)


class PuntoMapaSerializer(serializers.Serializer):
    codigo_iso = serializers.CharField()
    nombre = serializers.CharField()
    latitud = serializers.FloatField()
    longitud = serializers.FloatField()
    indice_compuesto = serializers.FloatField()
    nivel_riesgo = serializers.CharField()
    color = serializers.CharField()


class PuntoTendenciaSerializer(serializers.Serializer):
    anio = serializers.IntegerField()
    valor = serializers.FloatField()
