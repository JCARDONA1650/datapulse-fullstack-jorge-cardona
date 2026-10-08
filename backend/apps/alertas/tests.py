from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.paises.models import Pais, TipoCambio
from apps.riesgo.models import IndiceRiesgo
from apps.usuarios.models import Usuario

from .models import Alerta
from .services import (
    evaluar_alerta_inflacion,
    evaluar_alerta_tipo_cambio,
    evaluar_alertas_riesgo,
    generar_alertas_sincronizacion,
)


def crear_pais(**overrides):
    datos = {
        'codigo_iso': 'CO', 'nombre': 'Colombia', 'moneda_codigo': 'COP', 'moneda_nombre': 'Peso colombiano',
        'region': Pais.Region.ANDINA, 'latitud': 4.5709, 'longitud': -74.2973, 'poblacion': 52_000_000,
    }
    datos.update(overrides)
    return Pais.objects.create(**datos)


class ReglasAlertasTests(TestCase):
    def setUp(self):
        self.pais = crear_pais()

    def test_riesgo_critico(self):
        indice = IndiceRiesgo.objects.create(
            pais=self.pais, score_economico=10, score_cambiario=10, score_estabilidad=10,
            indice_compuesto=10, nivel_riesgo=IndiceRiesgo.NivelRiesgo.CRITICO, detalle_calculo={},
        )
        evaluar_alertas_riesgo(indice, None)
        alerta = Alerta.objects.get(pais=self.pais, tipo_alerta=Alerta.TipoAlerta.RIESGO)
        self.assertEqual(alerta.severidad, Alerta.Severidad.CRITICAL)

    def test_caida_fuerte_genera_warning(self):
        anterior = IndiceRiesgo.objects.create(
            pais=self.pais, score_economico=80, score_cambiario=80, score_estabilidad=80,
            indice_compuesto=80, nivel_riesgo=IndiceRiesgo.NivelRiesgo.BAJO, detalle_calculo={},
        )
        actual = IndiceRiesgo.objects.create(
            pais=self.pais, score_economico=60, score_cambiario=60, score_estabilidad=60,
            indice_compuesto=60, nivel_riesgo=IndiceRiesgo.NivelRiesgo.MODERADO, detalle_calculo={},
        )
        evaluar_alertas_riesgo(actual, anterior)
        self.assertTrue(
            Alerta.objects.filter(pais=self.pais, severidad=Alerta.Severidad.WARNING).exists(),
        )

    def test_caida_leve_no_genera_alerta(self):
        anterior = IndiceRiesgo.objects.create(
            pais=self.pais, score_economico=80, score_cambiario=80, score_estabilidad=80,
            indice_compuesto=80, nivel_riesgo=IndiceRiesgo.NivelRiesgo.BAJO, detalle_calculo={},
        )
        actual = IndiceRiesgo.objects.create(
            pais=self.pais, score_economico=75, score_cambiario=75, score_estabilidad=75,
            indice_compuesto=75, nivel_riesgo=IndiceRiesgo.NivelRiesgo.BAJO, detalle_calculo={},
        )
        evaluar_alertas_riesgo(actual, anterior)
        self.assertFalse(Alerta.objects.exists())

    def test_hiperinflacion(self):
        evaluar_alerta_inflacion(self.pais, 211.0)
        alerta = Alerta.objects.get()
        self.assertEqual(alerta.severidad, Alerta.Severidad.CRITICAL)
        self.assertEqual(alerta.tipo_alerta, Alerta.TipoAlerta.INDICADOR)

    def test_inflacion_normal_no_genera_alerta(self):
        evaluar_alerta_inflacion(self.pais, 9.2)
        self.assertFalse(Alerta.objects.exists())

    def test_variacion_tipo_cambio_fuerte(self):
        tipo_cambio = TipoCambio.objects.create(
            moneda_origen=self.pais, moneda_destino='USD', tasa=5000, fecha='2026-10-08',
            variacion_porcentual=4.5, fuente=TipoCambio.Fuente.MANUAL,
        )
        evaluar_alerta_tipo_cambio(tipo_cambio)
        alerta = Alerta.objects.get()
        self.assertEqual(alerta.severidad, Alerta.Severidad.WARNING)
        self.assertEqual(alerta.tipo_alerta, Alerta.TipoAlerta.TIPO_CAMBIO)

    def test_variacion_tipo_cambio_leve_no_genera_alerta(self):
        tipo_cambio = TipoCambio.objects.create(
            moneda_origen=self.pais, moneda_destino='USD', tasa=5000, fecha='2026-10-08',
            variacion_porcentual=1.2, fuente=TipoCambio.Fuente.MANUAL,
        )
        evaluar_alerta_tipo_cambio(tipo_cambio)
        self.assertFalse(Alerta.objects.exists())

    def test_sincronizacion_genera_alerta_info_por_pais(self):
        crear_pais(codigo_iso='BR', nombre='Brasil', moneda_codigo='BRL')
        alertas = generar_alertas_sincronizacion(['CO', 'BR'])
        self.assertEqual(len(alertas), 2)
        self.assertTrue(all(a.severidad == Alerta.Severidad.INFO for a in alertas))


class AlertaViewSetTests(APITestCase):
    def setUp(self):
        self.pais = crear_pais()
        self.usuario = Usuario.objects.create_user(
            email='u1@test.com', password='ClaveSegura123', nombre_completo='Usuario 1',
        )
        self.otro_usuario = Usuario.objects.create_user(
            email='u2@test.com', password='ClaveSegura123', nombre_completo='Usuario 2',
        )
        self.alerta_propia = Alerta.objects.create(
            usuario=self.usuario, pais=self.pais, tipo_alerta=Alerta.TipoAlerta.RIESGO,
            severidad=Alerta.Severidad.WARNING, titulo='Propia', mensaje='msg',
        )
        self.alerta_global = Alerta.objects.create(
            usuario=None, pais=self.pais, tipo_alerta=Alerta.TipoAlerta.INDICADOR,
            severidad=Alerta.Severidad.INFO, titulo='Global', mensaje='msg',
        )
        self.alerta_de_otro = Alerta.objects.create(
            usuario=self.otro_usuario, pais=self.pais, tipo_alerta=Alerta.TipoAlerta.RIESGO,
            severidad=Alerta.Severidad.CRITICAL, titulo='De otro usuario', mensaje='msg',
        )

    def test_lista_solo_propias_y_globales(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.get('/api/alertas/')
        titulos = {a['titulo'] for a in response.data['results']}
        self.assertEqual(titulos, {'Propia', 'Global'})

    def test_filtro_leida(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.get('/api/alertas/?leida=false')
        self.assertEqual(response.data['count'], 2)

    def test_marcar_leida(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.put(f'/api/alertas/{self.alerta_propia.id}/leer/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alerta_propia.refresh_from_db()
        self.assertTrue(self.alerta_propia.leida)

    def test_no_puede_marcar_alerta_de_otro_usuario(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.put(f'/api/alertas/{self.alerta_de_otro.id}/leer/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_marcar_todas_leidas(self):
        self.client.force_authenticate(self.usuario)
        self.client.put('/api/alertas/leer-todas/')
        self.assertFalse(Alerta.objects.filter(usuario=self.usuario, leida=False).exists())
        self.alerta_de_otro.refresh_from_db()
        self.assertFalse(self.alerta_de_otro.leida)

    def test_resumen(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.get('/api/alertas/resumen/')
        self.assertEqual(response.data['no_leidas'], 2)
        self.assertEqual(response.data['por_severidad']['WARNING'], 1)
        self.assertEqual(response.data['por_severidad']['INFO'], 1)
