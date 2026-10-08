from .models import LogActividad


def obtener_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def registrar_actividad(request, accion, entidad_afectada, entidad_id='', detalle=None):
    LogActividad.objects.create(
        usuario=request.user,
        accion=accion,
        entidad_afectada=entidad_afectada,
        entidad_id=str(entidad_id),
        detalle=detalle or {},
        ip_address=obtener_ip(request),
    )
