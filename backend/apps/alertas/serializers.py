from rest_framework import serializers

from .models import Alerta


class AlertaSerializer(serializers.ModelSerializer):
    pais = serializers.SlugRelatedField(slug_field='codigo_iso', read_only=True)
    pais_nombre = serializers.CharField(source='pais.nombre', read_only=True)

    class Meta:
        model = Alerta
        fields = [
            'id', 'usuario', 'pais', 'pais_nombre', 'tipo_alerta',
            'severidad', 'titulo', 'mensaje', 'leida', 'fecha_creacion',
        ]
        read_only_fields = fields
