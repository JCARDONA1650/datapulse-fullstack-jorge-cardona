from rest_framework import status
from rest_framework.test import APITestCase

from apps.alertas.models import Alerta
from apps.paises.models import IndicadorEconomico, Pais
from apps.portafolios.models import Portafolio
from apps.riesgo.models import IndiceRiesgo
from apps.usuarios.models import Usuario


def crear_pais(**overrides):
    datos = {
        'codigo_iso': 'CO', 'nombre': 'Colombia', 'moneda_codigo': 'COP', 'moneda_nombre': 'Peso colombiano',
        'region': Pais.Region.ANDINA, 'latitud': 4.5709, 'longitud': -74.2973, 'poblacion': 52_000_000,
    }
    datos.update(overrides)
    return Pais.objects.create(**datos)


class DashboardTests(APITestCase):
    def setUp(self):
        self.co = crear_pais()
        self.br = crear_pais(codigo_iso='BR', nombre='Brasil', moneda_codigo='BRL', region=Pais.Region.CONO_SUR)
        self.usuario = Usuario.objects.create_user(
            email='analista@test.com', password='ClaveSegura123', nombre_completo='Analista',
        )
        self.client.force_authenticate(self.usuario)

        IndiceRiesgo.objects.create(
            pais=self.co, score_economico=60, score_cambiario=90, score_estabilidad=80,
            indice_compuesto=75, nivel_riesgo=IndiceRiesgo.NivelRiesgo.BAJO, detalle_calculo={},
        )
        IndiceRiesgo.objects.create(
            pais=self.br, score_economico=40, score_cambiario=40, score_estabilidad=40,
            indice_compuesto=40, nivel_riesgo=IndiceRiesgo.NivelRiesgo.ALTO, detalle_calculo={},
        )
        Portafolio.objects.create(usuario=self.usuario, nombre='Cartera 1')
        Alerta.objects.create(
            usuario=None, pais=self.co, tipo_alerta=Alerta.TipoAlerta.RIESGO,
            severidad=Alerta.Severidad.WARNING, titulo='Alerta global', mensaje='msg',
        )
        IndicadorEconomico.objects.create(
            pais=self.co, tipo=IndicadorEconomico.Tipo.PIB_PERCAPITA, valor=6800, anio=2023,
            unidad=IndicadorEconomico.Unidad.USD, fuente=IndicadorEconomico.Fuente.MANUAL,
        )

    def test_resumen(self):
        response = self.client.get('/api/dashboard/resumen/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_paises_monitoreados'], 2)
        self.assertEqual(response.data['alertas_activas'], 1)
        self.assertEqual(response.data['portafolios_usuario'], 1)
        self.assertEqual(response.data['promedio_irpc_region'], 57.5)

    def test_mapa_incluye_color_y_coordenadas(self):
        response = self.client.get('/api/dashboard/mapa/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codigos = {fila['codigo_iso'] for fila in response.data}
        self.assertEqual(codigos, {'CO', 'BR'})
        co = next(fila for fila in response.data if fila['codigo_iso'] == 'CO')
        self.assertEqual(co['color'], '#22c55e')
        self.assertEqual(co['latitud'], 4.5709)

    def test_mapa_usa_solo_el_ultimo_calculo(self):
        IndiceRiesgo.objects.create(
            pais=self.co, score_economico=10, score_cambiario=10, score_estabilidad=10,
            indice_compuesto=10, nivel_riesgo=IndiceRiesgo.NivelRiesgo.CRITICO, detalle_calculo={},
        )
        response = self.client.get('/api/dashboard/mapa/')
        co = next(fila for fila in response.data if fila['codigo_iso'] == 'CO')
        self.assertEqual(co['nivel_riesgo'], 'CRITICO')

    def test_tendencias_filtra_por_tipo_y_paises(self):
        response = self.client.get('/api/dashboard/tendencias/?tipo=PIB_PERCAPITA&paises=CO')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('CO', response.data)
        self.assertEqual(response.data['CO'][0]['valor'], 6800.0)
        self.assertNotIn('BR', response.data)
