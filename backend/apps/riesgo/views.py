from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.core.permissions import EsAdmin

from .models import IndiceRiesgo
from .serializers import IndiceRiesgoSerializer
from .services import calcular_irpc_todos, ultimos_indices_queryset

CODIGO_ISO_PARAM = OpenApiParameter('codigo_iso', OpenApiTypes.STR, OpenApiParameter.PATH, description='Codigo ISO del pais (ej: CO)')


class RiesgoViewSet(GenericViewSet):
    serializer_class = IndiceRiesgoSerializer
    lookup_field = 'codigo_iso'

    def get_queryset(self):
        return IndiceRiesgo.objects.select_related('pais').all()

    def list(self, request):
        queryset = ultimos_indices_queryset().order_by('-indice_compuesto')
        pagina = self.paginate_queryset(queryset)
        serializer = self.get_serializer(pagina, many=True)
        return self.get_paginated_response(serializer.data)

    @extend_schema(parameters=[CODIGO_ISO_PARAM])
    def retrieve(self, request, codigo_iso=None):
        indice = (
            IndiceRiesgo.objects.filter(pais_id=codigo_iso)
            .select_related('pais')
            .order_by('-fecha_calculo')
            .first()
        )
        if indice is None:
            return Response(
                {'error': True, 'status_code': 404, 'mensaje': 'No hay calculo de riesgo para este pais.'},
                status=404,
            )
        serializer = self.get_serializer(indice)
        return Response(serializer.data)

    @extend_schema(parameters=[CODIGO_ISO_PARAM])
    @action(detail=True, methods=['get'])
    def historico(self, request, codigo_iso=None):
        queryset = (
            IndiceRiesgo.objects.filter(pais_id=codigo_iso).select_related('pais').order_by('-fecha_calculo')
        )

        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        if fecha_desde:
            queryset = queryset.filter(fecha_calculo__date__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_calculo__date__lte=fecha_hasta)

        pagina = self.paginate_queryset(queryset)
        serializer = self.get_serializer(pagina, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[EsAdmin])
    def calcular(self, request):
        resultados = calcular_irpc_todos()
        serializer = self.get_serializer(resultados, many=True)
        return Response(serializer.data)
