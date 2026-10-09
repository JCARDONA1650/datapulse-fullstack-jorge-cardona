from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.core.models import LogActividad
from apps.core.permissions import NoEsViewer
from apps.core.utils import registrar_actividad
from apps.usuarios.models import Usuario

from .models import Portafolio, Posicion
from .pdf import generar_pdf_portafolio
from .serializers import PortafolioDetalleSerializer, PortafolioSerializer, PosicionSerializer
from .services import calcular_resumen_portafolio


class PortafolioViewSet(viewsets.ModelViewSet):
    queryset = Portafolio.objects.none()
    search_fields = ['nombre']
    ordering_fields = ['nombre', 'fecha_creacion', 'fecha_modificacion']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PortafolioDetalleSerializer
        return PortafolioSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy', 'crear_posicion', 'gestionar_posicion'):
            return [permissions.IsAuthenticated(), NoEsViewer()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        usuario = self.request.user
        return (
            Portafolio.objects.filter(Q(usuario=usuario) | Q(es_publico=True), activo=True)
            .select_related('usuario')
        )

    def _verificar_permiso_edicion(self, instance):
        usuario = self.request.user
        if usuario.rol != Usuario.Rol.ADMIN and instance.usuario_id != usuario.id:
            raise PermissionDenied('Solo el propietario o un administrador puede modificar este portafolio.')

    def perform_create(self, serializer):
        portafolio = serializer.save(usuario=self.request.user)
        registrar_actividad(self.request, LogActividad.Accion.CREAR, 'Portafolio', portafolio.id)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        self._verificar_permiso_edicion(instance)

        fecha_esperada_raw = request.data.get('fecha_modificacion')
        if fecha_esperada_raw:
            fecha_esperada = parse_datetime(fecha_esperada_raw)
            if fecha_esperada is None or fecha_esperada != instance.fecha_modificacion:
                return Response(
                    {
                        'error': True, 'status_code': status.HTTP_409_CONFLICT,
                        'mensaje': 'Este portafolio fue modificado por otro usuario. Recarga los datos e intenta de nuevo.',
                    },
                    status=status.HTTP_409_CONFLICT,
                )

        response = super().update(request, *args, **kwargs)
        registrar_actividad(request, LogActividad.Accion.EDITAR, 'Portafolio', instance.id)
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self._verificar_permiso_edicion(instance)
        instance.activo = False
        instance.save(update_fields=['activo'])
        registrar_actividad(request, LogActividad.Accion.ELIMINAR, 'Portafolio', instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        portafolio = self.get_object()
        return Response(calcular_resumen_portafolio(portafolio))

    @action(detail=True, methods=['get'], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        portafolio = self.get_object()
        pdf_bytes = generar_pdf_portafolio(portafolio)
        registrar_actividad(request, LogActividad.Accion.EXPORT, 'Portafolio', portafolio.id)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="portafolio_{portafolio.id}.pdf"'
        return response

    @action(detail=True, methods=['post'], url_path='posiciones')
    def crear_posicion(self, request, pk=None):
        portafolio = self.get_object()
        self._verificar_permiso_edicion(portafolio)

        serializer = PosicionSerializer(data=request.data, context={'portafolio': portafolio})
        serializer.is_valid(raise_exception=True)
        posicion = serializer.save(portafolio=portafolio)
        registrar_actividad(request, LogActividad.Accion.CREAR, 'Posicion', posicion.id)
        return Response(PosicionSerializer(posicion).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put', 'delete'], url_path=r'posiciones/(?P<posicion_id>\d+)')
    def gestionar_posicion(self, request, pk=None, posicion_id=None):
        portafolio = self.get_object()
        self._verificar_permiso_edicion(portafolio)
        posicion = get_object_or_404(Posicion, pk=posicion_id, portafolio=portafolio)

        if request.method == 'DELETE':
            posicion.fecha_salida = timezone.now().date()
            posicion.save(update_fields=['fecha_salida'])
            registrar_actividad(request, LogActividad.Accion.ELIMINAR, 'Posicion', posicion.id)
            return Response(PosicionSerializer(posicion).data)

        serializer = PosicionSerializer(posicion, data=request.data, context={'portafolio': portafolio})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        registrar_actividad(request, LogActividad.Accion.EDITAR, 'Posicion', posicion.id)
        return Response(serializer.data)
