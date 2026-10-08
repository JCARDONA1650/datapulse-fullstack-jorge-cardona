from rest_framework import serializers

from .models import IndiceRiesgo
from .services import COLOR_POR_NIVEL


class IndiceRiesgoSerializer(serializers.ModelSerializer):
    pais = serializers.SlugRelatedField(slug_field='codigo_iso', read_only=True)
    pais_nombre = serializers.CharField(source='pais.nombre', read_only=True)
    color = serializers.SerializerMethodField()

    class Meta:
        model = IndiceRiesgo
        fields = [
            'id', 'pais', 'pais_nombre', 'fecha_calculo', 'score_economico', 'score_cambiario',
            'score_estabilidad', 'indice_compuesto', 'nivel_riesgo', 'color', 'detalle_calculo',
        ]

    def get_color(self, obj):
        return COLOR_POR_NIVEL.get(obj.nivel_riesgo)
