from django.conf import settings
from django.db import models


class LogActividad(models.Model):
    class Accion(models.TextChoices):
        CREAR = 'CREAR', 'Crear'
        EDITAR = 'EDITAR', 'Editar'
        ELIMINAR = 'ELIMINAR', 'Eliminar'
        CONSULTAR = 'CONSULTAR', 'Consultar'
        LOGIN = 'LOGIN', 'Login'
        EXPORT = 'EXPORT', 'Exportar'

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='logs_actividad')
    accion = models.CharField(max_length=10, choices=Accion.choices)
    entidad_afectada = models.CharField(max_length=100)
    entidad_id = models.CharField(max_length=50, blank=True)
    detalle = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['usuario', 'fecha']),
            models.Index(fields=['entidad_afectada', 'entidad_id']),
        ]
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.usuario} - {self.accion} - {self.entidad_afectada}'
