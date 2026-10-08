from unittest.mock import MagicMock, patch

from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.usuarios.models import Usuario

from .models import IndicadorEconomico, Pais, TipoCambio
from .services import sincronizar_indicadores, sincronizar_tipos_cambio


def crear_pais(**overrides):
    datos = {
        'codigo_iso': 'CO', 'nombre': 'Colombia', 'moneda_codigo': 'COP', 'moneda_nombre': 'Peso colombiano',
        'region': Pais.Region.ANDINA, 'latitud': 4.5709, 'longitud': -74.2973, 'poblacion': 52_000_000,
    }
    datos.update(overrides)
    return Pais.objects.create(**datos)


class PaisModelTests(TestCase):
    def test_moneda_codigo_unico(self):
        crear_pais()
        with self.assertRaises(IntegrityError):
            crear_pais(codigo_iso='XX', nombre='Otro', moneda_codigo='COP')


class IndicadorEconomicoModelTests(TestCase):
    def test_no_permite_duplicado_pais_tipo_anio(self):
        pais = crear_pais()
        IndicadorEconomico.objects.create(
            pais=pais, tipo=IndicadorEconomico.Tipo.INFLACION, valor=9.2,
            unidad=IndicadorEconomico.Unidad.PORCENTAJE, anio=2023, fuente=IndicadorEconomico.Fuente.MANUAL,
        )
        with self.assertRaises(IntegrityError):
            IndicadorEconomico.objects.create(
                pais=pais, tipo=IndicadorEconomico.Tipo.INFLACION, valor=10.0,
                unidad=IndicadorEconomico.Unidad.PORCENTAJE, anio=2023, fuente=IndicadorEconomico.Fuente.MANUAL,
            )


class TipoCambioModelTests(TestCase):
    def test_no_permite_duplicado_moneda_fecha(self):
        pais = crear_pais()
        TipoCambio.objects.create(
            moneda_origen=pais, moneda_destino='USD', tasa=4800, fecha='2026-10-01',
            fuente=TipoCambio.Fuente.MANUAL,
        )
        with self.assertRaises(IntegrityError):
            TipoCambio.objects.create(
                moneda_origen=pais, moneda_destino='USD', tasa=4810, fecha='2026-10-01',
                fuente=TipoCambio.Fuente.MANUAL,
            )


def _respuesta_world_bank(valor, anio):
    return MagicMock(
        status_code=200,
        json=lambda: [{'page': 1}, [{'date': str(anio), 'value': valor}]],
        raise_for_status=lambda: None,
    )


class SincronizarIndicadoresTests(TestCase):
    def setUp(self):
        self.pais = crear_pais()

    @patch('apps.paises.services.requests.get')
    def test_crea_indicadores_desde_world_bank(self, mock_get):
        mock_get.return_value = _respuesta_world_bank(9.2, 2023)

        resultado = sincronizar_indicadores()

        self.assertIn('CO', resultado['paises_procesados'])
        self.assertEqual(resultado['errores'], [])
        self.assertTrue(IndicadorEconomico.objects.filter(pais=self.pais, anio=2023).exists())

    @patch('apps.paises.services.requests.get')
    def test_continua_si_un_pais_falla(self, mock_get):
        crear_pais(codigo_iso='BR', nombre='Brasil', moneda_codigo='BRL')
        mock_get.side_effect = ConnectionError('timeout')

        resultado = sincronizar_indicadores()

        self.assertEqual(resultado['paises_procesados'], [])
        self.assertEqual(len(resultado['errores']), 2)


class SincronizarTiposCambioTests(TestCase):
    def setUp(self):
        self.pais = crear_pais()
        crear_pais(codigo_iso='EC', nombre='Ecuador', moneda_codigo='USD')

    @patch('apps.paises.services.requests.get')
    def test_crea_tipo_cambio_y_excluye_moneda_usd(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {'rates': {'COP': 4800.0}}, raise_for_status=lambda: None,
        )

        resultado = sincronizar_tipos_cambio()

        self.assertEqual(resultado['paises_procesados'], ['CO'])
        self.assertTrue(TipoCambio.objects.filter(moneda_origen=self.pais).exists())
        self.assertFalse(TipoCambio.objects.filter(moneda_origen_id='EC').exists())

    @patch('apps.paises.services.requests.get')
    def test_calcula_variacion_respecto_al_dia_anterior(self, mock_get):
        TipoCambio.objects.create(
            moneda_origen=self.pais, moneda_destino='USD', tasa=4800, fecha='2026-10-07',
            fuente=TipoCambio.Fuente.MANUAL,
        )
        mock_get.return_value = MagicMock(
            status_code=200, json=lambda: {'rates': {'COP': 4848.0}}, raise_for_status=lambda: None,
        )

        sincronizar_tipos_cambio()

        tipo_cambio_hoy = TipoCambio.objects.filter(moneda_origen=self.pais).order_by('-fecha').first()
        self.assertAlmostEqual(float(tipo_cambio_hoy.variacion_porcentual), 1.0, places=2)


class PaisViewSetTests(APITestCase):
    def setUp(self):
        crear_pais()
        crear_pais(codigo_iso='BR', nombre='Brasil', moneda_codigo='BRL', region=Pais.Region.CONO_SUR)
        self.analista = Usuario.objects.create_user(
            email='analista@test.com', password='ClaveSegura123', nombre_completo='Analista',
        )
        self.admin = Usuario.objects.create_user(
            email='admin@test.com', password='ClaveSegura123', nombre_completo='Admin', rol=Usuario.Rol.ADMIN,
        )

    def test_lista_paginada_y_filtro_region(self):
        self.client.force_authenticate(self.analista)
        response = self.client.get('/api/paises/?region=CONO_SUR')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['codigo_iso'], 'BR')

    def test_detalle_pais(self):
        self.client.force_authenticate(self.analista)
        response = self.client.get('/api/paises/CO/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], 'Colombia')

    def test_indicadores_filtra_por_tipo(self):
        pais = Pais.objects.get(codigo_iso='CO')
        IndicadorEconomico.objects.create(
            pais=pais, tipo=IndicadorEconomico.Tipo.INFLACION, valor=9.2,
            unidad=IndicadorEconomico.Unidad.PORCENTAJE, anio=2023, fuente=IndicadorEconomico.Fuente.MANUAL,
        )
        IndicadorEconomico.objects.create(
            pais=pais, tipo=IndicadorEconomico.Tipo.DESEMPLEO, valor=11.3,
            unidad=IndicadorEconomico.Unidad.PORCENTAJE, anio=2023, fuente=IndicadorEconomico.Fuente.MANUAL,
        )
        self.client.force_authenticate(self.analista)
        response = self.client.get('/api/paises/CO/indicadores/?tipo=INFLACION')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['tipo'], 'INFLACION')

    def test_sync_indicadores_requiere_admin(self):
        self.client.force_authenticate(self.analista)
        response = self.client.post('/api/paises/sync-indicadores/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.paises.services.requests.get')
    def test_sync_indicadores_permite_admin(self, mock_get):
        mock_get.return_value = _respuesta_world_bank(9.2, 2023)
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/paises/sync-indicadores/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
