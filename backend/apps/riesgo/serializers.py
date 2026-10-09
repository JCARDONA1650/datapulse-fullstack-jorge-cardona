from rest_framework import serializers

from .models import IndiceRiesgo
from .services import COLOR_POR_NIVEL


class IndiceRiesgoSerializer(serializers.ModelSerializer):
    pais = serializers.SlugRelatedField(slug_field='codigo_iso', read_only=True)
    pais_nombre = serializers.CharField(source='pais.nombre', read_only=True)
    color = serializers.SerializerMethodField()
    variacion = serializers.SerializerMethodField()

    class Meta:
        model = IndiceRiesgo
        fields = [
            'id', 'pais', 'pais_nombre', 'fecha_calculo', 'score_economico', 'score_cambiario',
            'score_estabilidad', 'indice_compuesto', 'nivel_riesgo', 'color', 'variacion', 'detalle_calculo',
        ]

    def get_color(self, obj) -> str:
        return COLOR_POR_NIVEL.get(obj.nivel_riesgo)

    def get_variacion(self, obj) -> float | None:
        anterior = (
            IndiceRiesgo.objects.filter(pais=obj.pais, fecha_calculo__lt=obj.fecha_calculo)
            .order_by('-fecha_calculo').first()
        )
        if anterior is None:
            return None
        return float(obj.indice_compuesto) - float(anterior.indice_compuesto)
