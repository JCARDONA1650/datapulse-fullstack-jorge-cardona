from django.db.models import Avg, Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alertas.models import Alerta
from apps.paises.models import IndicadorEconomico, Pais
from apps.portafolios.models import Portafolio
from apps.riesgo.services import COLOR_POR_NIVEL, ultimos_indices_queryset

from .serializers import PuntoMapaSerializer, ResumenDashboardSerializer

ANIOS_TENDENCIA = 5
MAXIMO_PAISES_COMPARACION = 3


class DashboardResumenView(APIView):
    @extend_schema(responses=ResumenDashboardSerializer)
    def get(self, request):
        total_paises = Pais.objects.filter(activo=True).count()

        alertas_activas = Alerta.objects.filter(
            Q(usuario=request.user) | Q(usuario__isnull=True), leida=False,
        ).count()

        portafolios_usuario = Portafolio.objects.filter(usuario=request.user, activo=True).count()

        promedio_irpc = ultimos_indices_queryset().aggregate(promedio=Avg('indice_compuesto'))['promedio']

        return Response({
            'total_paises_monitoreados': total_paises,
            'alertas_activas': alertas_activas,
            'portafolios_usuario': portafolios_usuario,
            'promedio_irpc_region': round(float(promedio_irpc), 2) if promedio_irpc is not None else None,
        })


class DashboardMapaView(APIView):
    @extend_schema(responses=PuntoMapaSerializer(many=True))
    def get(self, request):
        datos = [
            {
                'codigo_iso': indice.pais.codigo_iso,
                'nombre': indice.pais.nombre,
                'latitud': float(indice.pais.latitud),
                'longitud': float(indice.pais.longitud),
                'indice_compuesto': float(indice.indice_compuesto),
                'nivel_riesgo': indice.nivel_riesgo,
                'color': COLOR_POR_NIVEL.get(indice.nivel_riesgo),
            }
            for indice in ultimos_indices_queryset()
        ]
        return Response(datos)


class DashboardTendenciasView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter('tipo', OpenApiTypes.STR, description='Tipo de indicador (ej: PIB_PERCAPITA)'),
            OpenApiParameter('paises', OpenApiTypes.STR, description='Codigos ISO separados por coma, maximo 3'),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description='Retorna un objeto {codigo_iso: [{anio, valor}, ...]} por cada pais solicitado.',
    )
    def get(self, request):
        tipo = request.query_params.get('tipo', IndicadorEconomico.Tipo.PIB_PERCAPITA)
        codigos = request.query_params.get('paises', '')
        codigos_lista = [codigo.strip() for codigo in codigos.split(',') if codigo.strip()][:MAXIMO_PAISES_COMPARACION]

        desde = timezone.now().year - ANIOS_TENDENCIA
        queryset = IndicadorEconomico.objects.filter(tipo=tipo, anio__gte=desde)
        if codigos_lista:
            queryset = queryset.filter(pais_id__in=codigos_lista)

        resultado: dict[str, list[dict]] = {}
        for indicador in queryset.order_by('anio'):
            resultado.setdefault(indicador.pais_id, []).append({'anio': indicador.anio, 'valor': float(indicador.valor)})

        return Response(resultado)
