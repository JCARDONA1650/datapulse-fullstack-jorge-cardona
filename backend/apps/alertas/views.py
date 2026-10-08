from django.db.models import Count, Q
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Alerta
from .serializers import AlertaSerializer


class AlertaViewSet(ReadOnlyModelViewSet):
    serializer_class = AlertaSerializer
    filterset_fields = ['tipo_alerta', 'severidad', 'leida']

    def get_queryset(self):
        usuario = self.request.user
        return Alerta.objects.filter(Q(usuario=usuario) | Q(usuario__isnull=True)).select_related('pais')

    @action(detail=True, methods=['put'])
    def leer(self, request, pk=None):
        alerta = self.get_object()
        alerta.leida = True
        alerta.save(update_fields=['leida'])
        return Response(self.get_serializer(alerta).data)

    @action(detail=False, methods=['put'], url_path='leer-todas')
    def leer_todas(self, request):
        self.get_queryset().filter(leida=False).update(leida=True)
        return Response({'actualizado': True})

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        queryset = self.get_queryset()
        no_leidas = queryset.filter(leida=False).count()
        por_tipo = {fila['tipo_alerta']: fila['total'] for fila in queryset.values('tipo_alerta').annotate(total=Count('id'))}
        por_severidad = {fila['severidad']: fila['total'] for fila in queryset.values('severidad').annotate(total=Count('id'))}
        return Response({'no_leidas': no_leidas, 'por_tipo': por_tipo, 'por_severidad': por_severidad})
