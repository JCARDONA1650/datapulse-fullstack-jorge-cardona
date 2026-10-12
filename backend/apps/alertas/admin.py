from django.contrib import admin

from .models import Alerta


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'pais', 'tipo_alerta', 'severidad', 'leida', 'fecha_creacion')
    list_filter = ('tipo_alerta', 'severidad', 'leida')
    search_fields = ('titulo', 'pais__nombre')
