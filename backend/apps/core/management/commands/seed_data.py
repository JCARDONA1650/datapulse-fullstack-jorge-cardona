from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.alertas.models import Alerta
from apps.paises.models import Pais
from apps.paises.seed import crear_indicadores, crear_paises, crear_tipos_cambio
from apps.portafolios.seed import crear_portafolios
from apps.riesgo.models import IndiceRiesgo
from apps.riesgo.services import calcular_irpc_pais, clasificar_nivel_riesgo
from apps.usuarios.models import Usuario

# Dias hacia atras (desde hoy) de cada calculo historico del IRPC que se siembra por
# pais, para que el ranking tenga Variacion/Tendencia y el detalle tenga historico.
# El ajuste (puntos sobre el indice_compuesto real) hace que los calculos anteriores
# no sean identicos al actual (0 = sin ajuste), simulando una leve mejora en el tiempo.
DIAS_HISTORICO_IRPC = [(20, -3), (10, -1.5), (0, 0)]

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
        self.stdout.write('Indicadores economicos creados (5 anios por pais)')

        crear_tipos_cambio()
        self.stdout.write('Historico de tipo de cambio creado (30 dias)')

        IndiceRiesgo.objects.all().delete()
        Alerta.objects.all().delete()
        self.sembrar_historico_irpc()
        self.stdout.write('Indice de riesgo (IRPC) calculado para los 10 paises (3 fechas por pais)')

        crear_portafolios()
        self.stdout.write('Portafolios de ejemplo creados')

    def sembrar_historico_irpc(self):
        ahora = timezone.now()
        for pais in Pais.objects.filter(activo=True):
            for dias_atras, ajuste in DIAS_HISTORICO_IRPC:
                indice = calcular_irpc_pais(pais)
                cambios = {'fecha_calculo': ahora - timedelta(days=dias_atras)}
                if ajuste:
                    nuevo_indice = max(0, min(100, float(indice.indice_compuesto) + ajuste))
                    cambios['indice_compuesto'] = round(nuevo_indice, 2)
                    cambios['nivel_riesgo'] = clasificar_nivel_riesgo(nuevo_indice)
                IndiceRiesgo.objects.filter(pk=indice.pk).update(**cambios)

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
