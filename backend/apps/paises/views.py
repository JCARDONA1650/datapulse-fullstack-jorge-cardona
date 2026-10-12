from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.permissions import EsAdmin

from .models import Pais, TipoCambio
from .serializers import IndicadorEconomicoSerializer, PaisSerializer, TipoCambioSerializer
from .services import sincronizar_indicadores


class PaisViewSet(ReadOnlyModelViewSet):
    queryset = Pais.objects.filter(activo=True)
    serializer_class = PaisSerializer
    lookup_field = 'codigo_iso'
    filterset_fields = ['region']
    search_fields = ['nombre', 'codigo_iso']
    ordering_fields = ['nombre', 'poblacion', 'codigo_iso']

    @action(detail=True, methods=['get'])
    def indicadores(self, request, codigo_iso=None):
        pais = self.get_object()
        queryset = pais.indicadores.select_related('pais').all()

        tipo = request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        anio = request.query_params.get('anio')
        if anio:
            queryset = queryset.filter(anio=anio)

        queryset = queryset.order_by('-anio')
        pagina = self.paginate_queryset(queryset)
        serializer = IndicadorEconomicoSerializer(pagina, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'], url_path='tipo-cambio')
    def tipo_cambio(self, request, codigo_iso=None):
        pais = self.get_object()
        queryset = TipoCambio.objects.filter(moneda_origen=pais).select_related('moneda_origen')

        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)

        queryset = queryset.order_by('-fecha')
        pagina = self.paginate_queryset(queryset)
        serializer = TipoCambioSerializer(pagina, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post'], url_path='sync-indicadores', permission_classes=[EsAdmin])
    def sync_indicadores(self, request):
        resultado = sincronizar_indicadores()
        return Response(resultado, status=status.HTTP_200_OK)
