from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.paises.models import Pais
from apps.usuarios.models import Usuario

from .models import Portafolio, Posicion
from .services import calcular_resumen_portafolio, validar_posicion


def crear_pais(**overrides):
    datos = {
        'codigo_iso': 'CO', 'nombre': 'Colombia', 'moneda_codigo': 'COP', 'moneda_nombre': 'Peso colombiano',
        'region': Pais.Region.ANDINA, 'latitud': 4.5709, 'longitud': -74.2973, 'poblacion': 52_000_000,
    }
    datos.update(overrides)
    return Pais.objects.create(**datos)


class PortafolioModeloTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='analista@test.com', password='ClaveSegura123', nombre_completo='Analista',
        )

    def test_nombre_unico_por_usuario_activo(self):
        Portafolio.objects.create(usuario=self.usuario, nombre='Mi Cartera')
        with self.assertRaises(Exception):
            Portafolio.objects.create(usuario=self.usuario, nombre='Mi Cartera')

    def test_nombre_repetible_tras_soft_delete(self):
        p1 = Portafolio.objects.create(usuario=self.usuario, nombre='Mi Cartera')
        p1.activo = False
        p1.save()
        p2 = Portafolio.objects.create(usuario=self.usuario, nombre='Mi Cartera')
        self.assertTrue(p2.pk)


class ValidarPosicionTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='analista@test.com', password='ClaveSegura123', nombre_completo='Analista',
        )
        self.portafolio = Portafolio.objects.create(usuario=self.usuario, nombre='Cartera')
        self.co = crear_pais()
        self.ec = crear_pais(codigo_iso='EC', nombre='Ecuador', moneda_codigo='USD')

    def test_moneda_no_permitida_en_pais_dolarizado(self):
        with self.assertRaises(ValidationError):
            validar_posicion(self.portafolio, self.ec, Posicion.TipoActivo.MONEDA, 2000, date(2025, 1, 1), None)

    def test_fecha_entrada_futura_no_permitida(self):
        futura = date.today() + timedelta(days=5)
        with self.assertRaises(ValidationError):
            validar_posicion(self.portafolio, self.co, Posicion.TipoActivo.RENTA_FIJA, 2000, futura, None)

    def test_fecha_salida_debe_ser_posterior_a_entrada(self):
        with self.assertRaises(ValidationError):
            validar_posicion(
                self.portafolio, self.co, Posicion.TipoActivo.RENTA_FIJA, 2000,
                date(2025, 5, 1), date(2025, 1, 1),
            )

    def test_monto_maximo_portafolio(self):
        Posicion.objects.create(
            portafolio=self.portafolio, pais=self.co, tipo_activo=Posicion.TipoActivo.RENTA_FIJA,
            monto_inversion_usd=45_000_000, fecha_entrada=date(2025, 1, 1),
        )
        with self.assertRaises(ValidationError):
            validar_posicion(self.portafolio, self.co, Posicion.TipoActivo.RENTA_VARIABLE, 6_000_000, date(2025, 1, 1), None)

    def test_maximo_dos_posiciones_mismo_tipo_pais(self):
        for _ in range(2):
            Posicion.objects.create(
                portafolio=self.portafolio, pais=self.co, tipo_activo=Posicion.TipoActivo.RENTA_FIJA,
                monto_inversion_usd=1000, fecha_entrada=date(2025, 1, 1),
            )
        with self.assertRaises(ValidationError):
            validar_posicion(self.portafolio, self.co, Posicion.TipoActivo.RENTA_FIJA, 1000, date(2025, 1, 1), None)

    def test_posicion_cerrada_no_cuenta_para_limites(self):
        Posicion.objects.create(
            portafolio=self.portafolio, pais=self.co, tipo_activo=Posicion.TipoActivo.RENTA_FIJA,
            monto_inversion_usd=45_000_000, fecha_entrada=date(2025, 1, 1), fecha_salida=date(2025, 6, 1),
        )
        validar_posicion(self.portafolio, self.co, Posicion.TipoActivo.RENTA_VARIABLE, 6_000_000, date(2025, 1, 1), None)


class ResumenPortafolioTests(TestCase):
    def test_calcula_monto_total_y_distribucion(self):
        usuario = Usuario.objects.create_user(
            email='analista@test.com', password='ClaveSegura123', nombre_completo='Analista',
        )
        portafolio = Portafolio.objects.create(usuario=usuario, nombre='Cartera')
        co = crear_pais()
        br = crear_pais(codigo_iso='BR', nombre='Brasil', moneda_codigo='BRL')

        Posicion.objects.create(
            portafolio=portafolio, pais=co, tipo_activo=Posicion.TipoActivo.RENTA_FIJA,
            monto_inversion_usd=10000, fecha_entrada=date(2025, 1, 1),
        )
        Posicion.objects.create(
            portafolio=portafolio, pais=br, tipo_activo=Posicion.TipoActivo.RENTA_VARIABLE,
            monto_inversion_usd=5000, fecha_entrada=date(2025, 1, 1),
        )
        Posicion.objects.create(
            portafolio=portafolio, pais=co, tipo_activo=Posicion.TipoActivo.COMMODITIES,
            monto_inversion_usd=99999, fecha_entrada=date(2025, 1, 1), fecha_salida=date(2025, 2, 1),
        )

        resumen = calcular_resumen_portafolio(portafolio)
        self.assertEqual(resumen['monto_total_usd'], 15000.0)
        self.assertEqual(resumen['distribucion_por_pais']['CO'], 10000.0)
        self.assertEqual(resumen['distribucion_por_tipo_activo']['RENTA_VARIABLE'], 5000.0)


class PortafolioViewSetTests(APITestCase):
    def setUp(self):
        self.co = crear_pais()
        self.ec = crear_pais(codigo_iso='EC', nombre='Ecuador', moneda_codigo='USD')
        self.analista = Usuario.objects.create_user(
            email='analista@test.com', password='ClaveSegura123', nombre_completo='Analista',
        )
        self.otro_analista = Usuario.objects.create_user(
            email='otro@test.com', password='ClaveSegura123', nombre_completo='Otro',
        )
        self.admin = Usuario.objects.create_user(
            email='admin@test.com', password='ClaveSegura123', nombre_completo='Admin', rol=Usuario.Rol.ADMIN,
        )
        self.viewer = Usuario.objects.create_user(
            email='viewer@test.com', password='ClaveSegura123', nombre_completo='Viewer', rol=Usuario.Rol.VIEWER,
        )
        self.portafolio = Portafolio.objects.create(usuario=self.analista, nombre='Cartera', es_publico=True)

    def test_viewer_no_puede_crear(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post('/api/portafolios/', {'nombre': 'Nueva', 'descripcion': ''})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_crear_portafolio(self):
        self.client.force_authenticate(self.analista)
        response = self.client.post('/api/portafolios/', {'nombre': 'Otra Cartera', 'descripcion': 'desc'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['usuario'], self.analista.id)

    def test_no_permite_nombre_duplicado(self):
        self.client.force_authenticate(self.analista)
        response = self.client.post('/api/portafolios/', {'nombre': 'Cartera', 'descripcion': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lista_incluye_publicos_de_otros(self):
        self.client.force_authenticate(self.otro_analista)
        response = self.client.get('/api/portafolios/')
        self.assertEqual(response.data['count'], 1)
        self.assertFalse(response.data['results'][0]['es_propio'])

    def test_otro_analista_no_puede_editar(self):
        self.client.force_authenticate(self.otro_analista)
        response = self.client.put(f'/api/portafolios/{self.portafolio.id}/', {'nombre': 'Hackeada', 'descripcion': ''})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_puede_editar_portafolio_de_otro(self):
        self.client.force_authenticate(self.admin)
        response = self.client.put(
            f'/api/portafolios/{self.portafolio.id}/',
            {'nombre': 'Editada por admin', 'descripcion': '', 'es_publico': True},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_concurrencia_409(self):
        self.client.force_authenticate(self.analista)
        response = self.client.put(
            f'/api/portafolios/{self.portafolio.id}/',
            {'nombre': 'Cartera', 'descripcion': '', 'es_publico': True, 'fecha_modificacion': '2000-01-01T00:00:00Z'},
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_soft_delete(self):
        self.client.force_authenticate(self.analista)
        response = self.client.delete(f'/api/portafolios/{self.portafolio.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.portafolio.refresh_from_db()
        self.assertFalse(self.portafolio.activo)

    def test_crear_posicion_valida(self):
        self.client.force_authenticate(self.analista)
        response = self.client.post(
            f'/api/portafolios/{self.portafolio.id}/posiciones/',
            {'pais': 'CO', 'tipo_activo': 'RENTA_FIJA', 'monto_inversion_usd': 5000, 'fecha_entrada': '2025-01-01'},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_crear_posicion_moneda_usd_rechazada(self):
        self.client.force_authenticate(self.analista)
        response = self.client.post(
            f'/api/portafolios/{self.portafolio.id}/posiciones/',
            {'pais': 'EC', 'tipo_activo': 'MONEDA', 'monto_inversion_usd': 5000, 'fecha_entrada': '2025-01-01'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cerrar_posicion_asigna_fecha_salida(self):
        posicion = Posicion.objects.create(
            portafolio=self.portafolio, pais=self.co, tipo_activo=Posicion.TipoActivo.RENTA_FIJA,
            monto_inversion_usd=5000, fecha_entrada=date(2025, 1, 1),
        )
        self.client.force_authenticate(self.analista)
        response = self.client.delete(f'/api/portafolios/{self.portafolio.id}/posiciones/{posicion.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['fecha_salida'])

    def test_export_pdf(self):
        self.client.force_authenticate(self.analista)
        response = self.client.get(f'/api/portafolios/{self.portafolio.id}/export/pdf/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
