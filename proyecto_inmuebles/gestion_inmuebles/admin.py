from django.contrib import admin

from .models import Region, Comuna, Inmueble, Perfil


class RegionAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)


class ComunaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "region")
    search_fields = ("nombre", "region__nombre")
    list_filter = ("region",)


class InmuebleAdmin(admin.ModelAdmin):
    list_display = (
        "id", "nombre", "tipo_inmueble", "comuna",
        "precio_mensual", "estado", "propietario",
    )
    search_fields = ("nombre", "direccion", "comuna__nombre")
    list_filter = ("comuna__region", "comuna", "tipo_inmueble", "estado")


admin.site.register(Region, RegionAdmin)
admin.site.register(Comuna, ComunaAdmin)
admin.site.register(Inmueble, InmuebleAdmin)
admin.site.register(Perfil)