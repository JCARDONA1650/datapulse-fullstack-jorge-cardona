from django.core.management.base import BaseCommand

from apps.paises.services import sincronizar_indicadores


class Command(BaseCommand):
    help = 'Sincroniza los indicadores economicos de los 10 paises contra la API de World Bank.'

    def handle(self, *args, **options):
        resultado = sincronizar_indicadores()
        self.stdout.write(f"Paises procesados: {', '.join(resultado['paises_procesados'])}")
        if resultado['errores']:
            self.stdout.write(self.style.WARNING(f"Errores: {resultado['errores']}"))
