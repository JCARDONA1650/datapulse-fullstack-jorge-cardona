from django.contrib import admin

from .models import Portafolio, Posicion


class PosicionInline(admin.TabularInline):
    model = Posicion
    extra = 0


@admin.register(Portafolio)
class PortafolioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usuario', 'es_publico', 'activo', 'fecha_modificacion')
    list_filter = ('es_publico', 'activo')
    search_fields = ('nombre', 'usuario__email')
    inlines = [PosicionInline]
