from django.core.management.base import BaseCommand

from apps.alertas.models import Alerta
from apps.paises.seed import crear_indicadores, crear_paises, crear_tipos_cambio
from apps.portafolios.seed import crear_portafolios
from apps.riesgo.models import IndiceRiesgo
from apps.riesgo.services import calcular_irpc_todos
from apps.usuarios.models import Usuario

USUARIOS_INICIALES = [
    {'email': 'admin@datapulse.com', 'nombre_completo': 'Administrador DataPulse', 'rol': Usuario.Rol.ADMIN, 'is_staff': True, 'is_superuser': True},
    {'email': 'analista@datapulse.com', 'nombre_completo': 'Analista DataPulse', 'rol': Usuario.Rol.ANALISTA},
    {'email': 'viewer@datapulse.com', 'nombre_completo': 'Viewer DataPulse', 'rol': Usuario.Rol.VIEWER},
]
PASSWORD_INICIAL = 'DataPulse2026!'


class Command(BaseCommand):
    help = 'Crea los datos iniciales de DataPulse Latam (usuarios, paises, indicadores, portafolios).'

    def handle(self, *args, **options):
        self.crear_usuarios()

        crear_paises()
        self.stdout.write('Paises creados')

        crear_indicadores()
        self.stdout.write('Indicadores economicos creados (3 anios por pais)')

        crear_tipos_cambio()
        self.stdout.write('Historico de tipo de cambio creado (30 dias)')

        IndiceRiesgo.objects.all().delete()
        Alerta.objects.all().delete()
        calcular_irpc_todos()
        self.stdout.write('Indice de riesgo (IRPC) calculado para los 10 paises')

        crear_portafolios()
        self.stdout.write('Portafolios de ejemplo creados')

    def crear_usuarios(self):
        for datos in USUARIOS_INICIALES:
            usuario, creado = Usuario.objects.get_or_create(
                email=datos['email'],
                defaults={k: v for k, v in datos.items() if k != 'email'},
            )
            if creado:
                usuario.set_password(PASSWORD_INICIAL)
                usuario.save()
                self.stdout.write(f'Usuario creado: {usuario.email} ({usuario.rol})')
            else:
                self.stdout.write(f'Usuario ya existia: {usuario.email}')
