from django.core.management import call_command
from django.test import TestCase

from apps.paises.models import IndicadorEconomico, Pais, TipoCambio
from apps.riesgo.models import IndiceRiesgo


class SeedDataIdempotenteTests(TestCase):
    """seed_data debe poder correr en cada arranque del contenedor sin pisar datos
    reales (p. ej. los que trajo un admin con "Sincronizar indicadores")."""

    def test_crea_usuarios_paises_e_indicadores_en_una_base_vacia(self):
        call_command('seed_data')

        self.assertEqual(Pais.objects.count(), 10)
        self.assertTrue(IndicadorEconomico.objects.filter(pais_id='CO', anio=2023).exists())
        self.assertTrue(IndiceRiesgo.objects.filter(pais_id='CO').exists())
        self.assertTrue(TipoCambio.objects.filter(moneda_origen_id='COP').exists())

    def test_no_reescribe_un_indicador_ya_existente(self):
        call_command('seed_data')
        indicador = IndicadorEconomico.objects.get(pais_id='CO', tipo=IndicadorEconomico.Tipo.INFLACION, anio=2023)
        indicador.valor = 999
        indicador.save()

        call_command('seed_data')

        indicador.refresh_from_db()
        self.assertEqual(float(indicador.valor), 999.0)

    def test_no_borra_ni_recalcula_el_irpc_si_la_tabla_ya_tiene_datos(self):
        call_command('seed_data')
        total_antes = IndiceRiesgo.objects.count()
        indice = IndiceRiesgo.objects.filter(pais_id='CO').first()
        indice.indice_compuesto = 1.23
        indice.save()

        call_command('seed_data')

        self.assertEqual(IndiceRiesgo.objects.count(), total_antes)
        indice.refresh_from_db()
        self.assertEqual(float(indice.indice_compuesto), 1.23)

    def test_no_borra_ni_reescribe_el_tipo_de_cambio_existente(self):
        call_command('seed_data')
        total_antes = TipoCambio.objects.count()
        tipo_cambio = TipoCambio.objects.filter(moneda_origen_id='COP').first()
        tipo_cambio.tasa = 1.0
        tipo_cambio.save()

        call_command('seed_data')

        self.assertEqual(TipoCambio.objects.count(), total_antes)
        tipo_cambio.refresh_from_db()
        self.assertEqual(float(tipo_cambio.tasa), 1.0)
