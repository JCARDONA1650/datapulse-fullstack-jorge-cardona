from django.contrib import admin

from .models import IndiceRiesgo


@admin.register(IndiceRiesgo)
class IndiceRiesgoAdmin(admin.ModelAdmin):
    list_display = ('pais', 'fecha_calculo', 'indice_compuesto', 'nivel_riesgo')
    list_filter = ('nivel_riesgo',)
    search_fields = ('pais__nombre',)
