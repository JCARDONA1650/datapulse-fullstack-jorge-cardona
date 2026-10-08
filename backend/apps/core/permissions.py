from rest_framework.permissions import BasePermission

from apps.usuarios.models import Usuario


class EsAdmin(BasePermission):
    message = 'Esta accion requiere rol de administrador.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.rol == Usuario.Rol.ADMIN)


class NoEsViewer(BasePermission):
    message = 'Los usuarios con rol viewer no pueden realizar esta accion.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.rol != Usuario.Rol.VIEWER)
