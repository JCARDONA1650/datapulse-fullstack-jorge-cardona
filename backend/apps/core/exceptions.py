from rest_framework.views import exception_handler


def manejador_excepciones(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    detalle = response.data
    if isinstance(detalle, dict) and list(detalle.keys()) == ['detail']:
        detalle = detalle['detail']

    response.data = {
        'error': True,
        'status_code': response.status_code,
        'mensaje': detalle,
    }
    return response
