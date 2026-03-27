from django.contrib import admin

from .models import (
    GUF,
    DesignInstallation,
    DesignLoop,
    DesignSurfaceInfiltration,
    DesignWell,
    EnergyCharacteristics,
    GUFEvent,
)


class GUFAdmin(admin.ModelAdmin):
    model = GUF
    list_display = (
        "bro_id",
        "data_owner",
        "delivery_accountable_party",
        "quality_regime",
    )
    list_filter = ("data_owner", "quality_regime", "delivery_context")


class DesignInstallationAdmin(admin.ModelAdmin):
    model = DesignInstallation
    list_display = (
        "guf",
        "design_installation_id",
        "installation_function",
        "data_owner",
    )
    list_filter = ("data_owner", "installation_function")
    raw_id_fields = ("guf",)


class EnergyCharacteristicsAdmin(admin.ModelAdmin):
    model = EnergyCharacteristics
    list_display = (
        "installation",
        "energy_cold",
        "energy_warm",
        "data_owner",
    )
    list_filter = ("data_owner",)
    raw_id_fields = ("installation",)


class DesignLoopAdmin(admin.ModelAdmin):
    model = DesignLoop
    list_display = (
        "installation",
        "design_loop_id",
        "loop_type",
        "data_owner",
    )
    list_filter = ("data_owner", "loop_type", "geometry_type")
    raw_id_fields = ("installation",)


class DesignWellAdmin(admin.ModelAdmin):
    model = DesignWell
    list_display = (
        "installation",
        "design_well_id",
        "height",
        "data_owner",
    )
    list_filter = ("data_owner", "geometry_publicly_available", "relative_temperature")
    raw_id_fields = ("installation",)


class DesignSurfaceInfiltrationAdmin(admin.ModelAdmin):
    model = DesignSurfaceInfiltration
    list_display = (
        "installation",
        "design_surface_infiltration_id",
        "data_owner",
    )
    list_filter = ("data_owner",)
    raw_id_fields = ("installation",)


class GUFEventAdmin(admin.ModelAdmin):
    model = GUFEvent
    list_display = (
        "guf",
        "event_name",
        "event_date",
        "data_owner",
    )
    list_filter = ("data_owner", "event_name")
    raw_id_fields = ("guf",)


admin.site.register(GUF, GUFAdmin)
admin.site.register(DesignInstallation, DesignInstallationAdmin)
admin.site.register(EnergyCharacteristics, EnergyCharacteristicsAdmin)
admin.site.register(DesignLoop, DesignLoopAdmin)
admin.site.register(DesignWell, DesignWellAdmin)
admin.site.register(DesignSurfaceInfiltration, DesignSurfaceInfiltrationAdmin)
admin.site.register(GUFEvent, GUFEventAdmin)
