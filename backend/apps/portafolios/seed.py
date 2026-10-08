from datetime import date

from apps.paises.models import Pais
from apps.usuarios.models import Usuario

from .models import Portafolio, Posicion

PORTAFOLIOS_SEED = [
    {
        'nombre': 'Cartera LatAm Diversificada',
        'descripcion': 'Portafolio de ejemplo con posiciones en varios paises y tipos de activo.',
        'es_publico': True,
        'posiciones': [
            ('CO', Posicion.TipoActivo.RENTA_FIJA, 15_000_000, date(2025, 1, 15)),
            ('BR', Posicion.TipoActivo.RENTA_VARIABLE, 10_000_000, date(2025, 3, 1)),
            ('MX', Posicion.TipoActivo.COMMODITIES, 5_000_000, date(2025, 2, 10)),
            ('CL', Posicion.TipoActivo.MONEDA, 3_000_000, date(2025, 4, 1)),
        ],
    },
    {
        'nombre': 'Cobertura Cambiaria',
        'descripcion': 'Portafolio privado de ejemplo enfocado en cobertura de monedas.',
        'es_publico': False,
        'posiciones': [
            ('AR', Posicion.TipoActivo.MONEDA, 2_000_000, date(2025, 5, 1)),
            ('PE', Posicion.TipoActivo.RENTA_FIJA, 4_000_000, date(2025, 6, 1)),
        ],
    },
]


def crear_portafolios():
    """update_or_create + se borran las posiciones antes de recrearlas para que el seed sea
    reproducible aunque se hayan hecho pruebas manuales (ediciones, cierres, soft-delete) encima."""
    analista = Usuario.objects.get(email='analista@datapulse.com')

    for datos in PORTAFOLIOS_SEED:
        portafolio, _ = Portafolio.objects.update_or_create(
            usuario=analista, nombre=datos['nombre'],
            defaults={'descripcion': datos['descripcion'], 'es_publico': datos['es_publico'], 'activo': True},
        )
        portafolio.posiciones.all().delete()

        for codigo_iso, tipo_activo, monto, fecha_entrada in datos['posiciones']:
            Posicion.objects.create(
                portafolio=portafolio, pais=Pais.objects.get(codigo_iso=codigo_iso), tipo_activo=tipo_activo,
                monto_inversion_usd=monto, fecha_entrada=fecha_entrada,
            )
