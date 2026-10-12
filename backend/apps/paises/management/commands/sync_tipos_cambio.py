from django.core.management.base import BaseCommand

from apps.paises.services import sincronizar_tipos_cambio


class Command(BaseCommand):
    help = 'Sincroniza las tasas de cambio diarias contra ExchangeRate-API.'

    def handle(self, *args, **options):
        resultado = sincronizar_tipos_cambio()
        self.stdout.write(f"Paises procesados: {', '.join(resultado['paises_procesados'])}")
        if resultado['errores']:
            self.stdout.write(self.style.WARNING(f"Errores: {resultado['errores']}"))
