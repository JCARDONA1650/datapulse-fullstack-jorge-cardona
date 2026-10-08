from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.paises.models import IndicadorEconomico, Pais, TipoCambio
from apps.usuarios.models import Usuario

from .models import IndiceRiesgo
from .services import (
    calcular_crecimiento_pib,
    calcular_depreciacion_acumulada,
    calcular_irpc_pais,
    calcular_volatilidad,
    clasificar_nivel_riesgo,
    contar_indicadores_en_riesgo,
    score_cambiario,
    score_economico,
    score_estabilidad,
)


class CasoObligatorioColombiaTests(TestCase):
    """
    Reproduce el caso de prueba de HU_GLOBAL.md (Epica 4) con las entradas
    literales. Con la formula tal como esta escrita (ver documentacion/INCONSISTENCIAS.md,
    punto 1), el resultado real difiere del que indica el documento: Score Economico=60
    (no 45) porque Inflacion=9.2 cae en el bracket >5 (-10), no en >10 (-25). El resto de
    los valores si coincide con el documento.
    """

    def test_score_economico(self):
        score, detalle = score_economico(pib_percapita=6800, inflacion=9.2, desempleo=11.3, deuda_pib=55)
        self.assertEqual(score, 60)
        self.assertEqual(detalle['penalizaciones']['PIB_PERCAPITA'], -5)
        self.assertEqual(detalle['penalizaciones']['INFLACION'], -10)
        self.assertEqual(detalle['penalizaciones']['DESEMPLEO'], -15)
        self.assertEqual(detalle['penalizaciones']['DEUDA_PIB'], -10)

    def test_indicadores_en_riesgo(self):
        _, detalle = score_economico(pib_percapita=6800, inflacion=9.2, desempleo=11.3, deuda_pib=55)
        self.assertEqual(contar_indicadores_en_riesgo(detalle), 3)

    def test_score_cambiario(self):
        score, detalle = score_cambiario(volatilidad=0.8, depreciacion=1.5)
        self.assertEqual(score, 90)
        self.assertEqual(detalle['penalizaciones']['VOLATILIDAD'], -10)
        self.assertNotIn('DEPRECIACION', detalle['penalizaciones'])

    def test_score_estabilidad(self):
        score, detalle = score_estabilidad(balanza_comercial=-4.2, crecimiento_pib=1.5, indicadores_en_riesgo=3)
        self.assertEqual(score, 80)
        self.assertEqual(detalle['penalizaciones']['BALANZA_COMERCIAL'], -5)
        self.assertEqual(detalle['penalizaciones']['INDICADORES_EN_RIESGO'], -15)
        self.assertNotIn('CRECIMIENTO_PIB', detalle['penalizaciones'])

    def test_irpc_compuesto_real_vs_documento(self):
        economico, _ = score_economico(pib_percapita=6800, inflacion=9.2, desempleo=11.3, deuda_pib=55)
        cambiario, _ = score_cambiario(volatilidad=0.8, depreciacion=1.5)
        estabilidad, _ = score_estabilidad(balanza_comercial=-4.2, crecimiento_pib=1.5, indicadores_en_riesgo=3)
        indice = round(economico * 0.40 + cambiario * 0.30 + estabilidad * 0.30, 2)

        self.assertEqual(indice, 75.0)
        self.assertEqual(clasificar_nivel_riesgo(indice), IndiceRiesgo.NivelRiesgo.BAJO)


class ScoreFuncionesTests(TestCase):
    def test_datos_incompletos_no_penaliza_y_registra_faltante(self):
        score, detalle = score_economico(pib_percapita=None, inflacion=9.2, desempleo=11.3, deuda_pib=55)
        self.assertEqual(score, 65)
        self.assertIn('PIB_PERCAPITA', detalle['faltantes'])

    def test_clasificacion_bordes(self):
        self.assertEqual(clasificar_nivel_riesgo(75), IndiceRiesgo.NivelRiesgo.BAJO)
        self.assertEqual(clasificar_nivel_riesgo(74.99), IndiceRiesgo.NivelRiesgo.MODERADO)
        self.assertEqual(clasificar_nivel_riesgo(50), IndiceRiesgo.NivelRiesgo.MODERADO)
        self.assertEqual(clasificar_nivel_riesgo(49.99), IndiceRiesgo.NivelRiesgo.ALTO)
        self.assertEqual(clasificar_nivel_riesgo(25), IndiceRiesgo.NivelRiesgo.ALTO)
        self.assertEqual(clasificar_nivel_riesgo(24.99), IndiceRiesgo.NivelRiesgo.CRITICO)

    def test_score_nunca_baja_de_cero(self):
        score, _ = score_economico(pib_percapita=1000, inflacion=60, desempleo=20, deuda_pib=90)
        self.assertEqual(score, 0)

    def test_volatilidad_requiere_al_menos_dos_variaciones(self):
        self.assertIsNone(calcular_volatilidad([4800]))
        self.assertIsNotNone(calcular_volatilidad([4800, 4850, 4820, 4900]))

    def test_depreciacion_primera_vs_ultima(self):
        resultado = calcular_depreciacion_acumulada([100, 101, 99, 102])
        self.assertAlmostEqual(resultado, 2.0, places=4)

    def test_crecimiento_pib(self):
        self.assertAlmostEqual(calcular_crecimiento_pib(355.25, 350), 1.5, places=4)
        self.assertIsNone(calcular_crecimiento_pib(355.25, None))


class CalcularIrpcPaisTests(TestCase):
    def setUp(self):
        self.pais = Pais.objects.create(
            codigo_iso='CO', nombre='Colombia', moneda_codigo='COP', moneda_nombre='Peso colombiano',
            region=Pais.Region.ANDINA, latitud=4.5709, longitud=-74.2973, poblacion=52_000_000,
        )
        datos = [
            (IndicadorEconomico.Tipo.PIB_PERCAPITA, 6800, 2023),
            (IndicadorEconomico.Tipo.INFLACION, 9.2, 2023),
            (IndicadorEconomico.Tipo.DESEMPLEO, 11.3, 2023),
            (IndicadorEconomico.Tipo.DEUDA_PIB, 55, 2023),
            (IndicadorEconomico.Tipo.BALANZA_COMERCIAL, -4.2, 2023),
            (IndicadorEconomico.Tipo.PIB, 355.25, 2023),
            (IndicadorEconomico.Tipo.PIB, 350, 2022),
        ]
        for tipo, valor, anio in datos:
            IndicadorEconomico.objects.create(
                pais=self.pais, tipo=tipo, valor=valor, anio=anio,
                unidad=IndicadorEconomico.Unidad.PORCENTAJE, fuente=IndicadorEconomico.Fuente.MANUAL,
            )
        for i, tasa in enumerate([4800, 4810, 4790, 4805]):
            TipoCambio.objects.create(
                moneda_origen=self.pais, moneda_destino='USD', tasa=tasa, fecha=f'2026-10-0{i + 1}',
                fuente=TipoCambio.Fuente.MANUAL,
            )

    def test_calcula_y_guarda_indice_riesgo(self):
        indice = calcular_irpc_pais(self.pais)
        self.assertEqual(indice.score_economico, 60)
        self.assertEqual(indice.detalle_calculo['crecimiento_pib'], 1.5)
        self.assertTrue(IndiceRiesgo.objects.filter(pais=self.pais).exists())

    def test_pais_dolarizado_score_cambiario_fijo(self):
        ecuador = Pais.objects.create(
            codigo_iso='EC', nombre='Ecuador', moneda_codigo='USD', moneda_nombre='Dolar',
            region=Pais.Region.ANDINA, latitud=-1.83, longitud=-78.18, poblacion=18_000_000,
        )
        indice = calcular_irpc_pais(ecuador)
        self.assertEqual(indice.score_cambiario, 100)


class RiesgoViewSetTests(APITestCase):
    def setUp(self):
        self.pais = Pais.objects.create(
            codigo_iso='CO', nombre='Colombia', moneda_codigo='COP', moneda_nombre='Peso colombiano',
            region=Pais.Region.ANDINA, latitud=4.5709, longitud=-74.2973, poblacion=52_000_000,
        )
        IndiceRiesgo.objects.create(
            pais=self.pais, score_economico=60, score_cambiario=90, score_estabilidad=80,
            indice_compuesto=75, nivel_riesgo=IndiceRiesgo.NivelRiesgo.BAJO, detalle_calculo={},
        )
        self.analista = Usuario.objects.create_user(
            email='analista@test.com', password='ClaveSegura123', nombre_completo='Analista',
        )
        self.admin = Usuario.objects.create_user(
            email='admin@test.com', password='ClaveSegura123', nombre_completo='Admin', rol=Usuario.Rol.ADMIN,
        )

    def test_ranking(self):
        self.client.force_authenticate(self.analista)
        response = self.client.get('/api/riesgo/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['pais'], 'CO')

    def test_detalle_pais(self):
        self.client.force_authenticate(self.analista)
        response = self.client.get('/api/riesgo/CO/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nivel_riesgo'], 'BAJO')

    def test_calcular_requiere_admin(self):
        self.client.force_authenticate(self.analista)
        response = self.client.post('/api/riesgo/calcular/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_calcular_permite_admin(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/riesgo/calcular/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
