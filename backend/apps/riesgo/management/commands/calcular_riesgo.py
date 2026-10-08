from django.core.management.base import BaseCommand

from apps.riesgo.services import calcular_irpc_todos


class Command(BaseCommand):
    help = 'Calcula el Indice de Riesgo Pais Compuesto (IRPC) de los 10 paises.'

    def handle(self, *args, **options):
        resultados = calcular_irpc_todos()
        for indice in resultados:
            self.stdout.write(f'{indice.pais_id}: {indice.indice_compuesto} ({indice.nivel_riesgo})')
