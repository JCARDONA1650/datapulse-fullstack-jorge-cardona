from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.paises.models import Pais

from .models import Portafolio, Posicion
from .services import validar_posicion


class PosicionSerializer(serializers.ModelSerializer):
    pais = serializers.PrimaryKeyRelatedField(queryset=Pais.objects.filter(activo=True))
    pais_nombre = serializers.CharField(source='pais.nombre', read_only=True)

    class Meta:
        model = Posicion
        fields = [
            'id', 'portafolio', 'pais', 'pais_nombre', 'tipo_activo',
            'monto_inversion_usd', 'fecha_entrada', 'fecha_salida', 'notas',
        ]
        read_only_fields = ['id', 'portafolio', 'fecha_salida']

    def validate(self, datos):
        portafolio = self.context['portafolio']
        pais = datos.get('pais', getattr(self.instance, 'pais', None))
        tipo_activo = datos.get('tipo_activo', getattr(self.instance, 'tipo_activo', None))
        monto = datos.get('monto_inversion_usd', getattr(self.instance, 'monto_inversion_usd', None))
        fecha_entrada = datos.get('fecha_entrada', getattr(self.instance, 'fecha_entrada', None))
        fecha_salida = getattr(self.instance, 'fecha_salida', None)

        try:
            validar_posicion(
                portafolio, pais, tipo_activo, monto, fecha_entrada, fecha_salida, posicion_actual=self.instance,
            )
        except DjangoValidationError as exc:
            detalle = exc.message_dict if hasattr(exc, 'message_dict') else {'detail': exc.messages}
            raise serializers.ValidationError(detalle)

        return datos


class PortafolioSerializer(serializers.ModelSerializer):
    es_propio = serializers.SerializerMethodField()

    class Meta:
        model = Portafolio
        fields = [
            'id', 'nombre', 'descripcion', 'usuario', 'es_propio',
            'fecha_creacion', 'fecha_modificacion', 'activo', 'es_publico',
        ]
        read_only_fields = ['id', 'usuario', 'fecha_creacion', 'fecha_modificacion', 'activo']

    def get_es_propio(self, obj) -> bool:
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and obj.usuario_id == request.user.id)

    def validate(self, datos):
        request = self.context.get('request')
        nombre = datos.get('nombre', getattr(self.instance, 'nombre', None))

        if request and nombre:
            queryset = Portafolio.objects.filter(usuario=request.user, nombre__iexact=nombre, activo=True)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({'nombre': 'Ya tienes un portafolio activo con este nombre.'})

        return datos


class PortafolioDetalleSerializer(PortafolioSerializer):
    posiciones = PosicionSerializer(many=True, read_only=True)

    class Meta(PortafolioSerializer.Meta):
        fields = PortafolioSerializer.Meta.fields + ['posiciones']
