import logging
import time

logger = logging.getLogger('apps.requests')


class LoggingRequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        inicio = time.monotonic()
        response = self.get_response(request)
        duracion_ms = (time.monotonic() - inicio) * 1000

        usuario = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'anonimo'
        logger.info(
            '%s %s usuario=%s status=%s duracion_ms=%.1f',
            request.method,
            request.path,
            usuario,
            response.status_code,
            duracion_ms,
        )
        return response
