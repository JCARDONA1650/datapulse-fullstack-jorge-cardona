from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    ordering = ('email',)
    list_display = ('email', 'nombre_completo', 'rol', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informacion personal', {'fields': ('nombre_completo', 'rol')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'fecha_creacion')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'nombre_completo', 'rol', 'password1', 'password2')}),
    )
    readonly_fields = ('fecha_creacion',)
    search_fields = ('email', 'nombre_completo')
