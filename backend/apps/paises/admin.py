from django.contrib import admin

from .models import IndicadorEconomico, Pais, TipoCambio


@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ('codigo_iso', 'nombre', 'moneda_codigo', 'region', 'poblacion', 'activo')
    search_fields = ('codigo_iso', 'nombre')
    list_filter = ('region', 'activo')


@admin.register(IndicadorEconomico)
class IndicadorEconomicoAdmin(admin.ModelAdmin):
    list_display = ('pais', 'tipo', 'anio', 'valor', 'fuente')
    list_filter = ('tipo', 'fuente', 'anio')
    search_fields = ('pais__nombre',)


@admin.register(TipoCambio)
class TipoCambioAdmin(admin.ModelAdmin):
    list_display = ('moneda_origen', 'fecha', 'tasa', 'variacion_porcentual', 'fuente')
    list_filter = ('fuente',)
