from rest_framework import serializers

from .models import IndicadorEconomico, Pais, TipoCambio


class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = [
            'codigo_iso', 'nombre', 'moneda_codigo', 'moneda_nombre',
            'region', 'latitud', 'longitud', 'poblacion', 'activo',
        ]


class IndicadorEconomicoSerializer(serializers.ModelSerializer):
    pais = serializers.SlugRelatedField(slug_field='codigo_iso', read_only=True)

    class Meta:
        model = IndicadorEconomico
        fields = ['id', 'pais', 'tipo', 'valor', 'unidad', 'anio', 'fuente', 'fecha_actualizacion']


class TipoCambioSerializer(serializers.ModelSerializer):
    moneda_origen = serializers.SlugRelatedField(slug_field='moneda_codigo', read_only=True)

    class Meta:
        model = TipoCambio
        fields = ['id', 'moneda_origen', 'moneda_destino', 'tasa', 'fecha', 'variacion_porcentual', 'fuente']
