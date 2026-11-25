from django.contrib import admin

from .models import (
    FRD,
    GeoElectricMeasure,
    GeoElectricMeasurement,
    MeasurementConfiguration,
)


class FRDAdmin(admin.ModelAdmin):
    model = FRD
    list_display = (
        "bro_id",
        "data_owner",
    )
    list_select_related = ("data_owner",)
    list_filter = ("data_owner",)
    search_fields = ("bro_id", "gmw_bro_id")
    # Avoids rendering a dropdown with every monitoring tube.
    autocomplete_fields = ("monitoring_tube",)


class MeasurementConfigurationAdmin(admin.ModelAdmin):
    model = MeasurementConfiguration
    list_display = (
        "frd",
        "data_owner",
    )
    list_select_related = ("frd", "data_owner")
    list_filter = ("data_owner",)
    raw_id_fields = ("frd",)


class GeoElectricMeasurementAdmin(admin.ModelAdmin):
    model = GeoElectricMeasurement
    list_display = (
        "frd",
        "measurement_date",
        "data_owner",
    )
    list_select_related = ("frd", "data_owner")
    list_filter = ("data_owner",)
    raw_id_fields = ("frd",)


class GeoElectricMeasureAdmin(admin.ModelAdmin):
    model = GeoElectricMeasure
    list_display = (
        "geo_electric_measurement",
        "resistance",
        "data_owner",
    )
    list_select_related = ("geo_electric_measurement__frd", "data_owner")
    list_filter = ("data_owner",)
    raw_id_fields = ("geo_electric_measurement",)


admin.site.register(FRD, FRDAdmin)
admin.site.register(MeasurementConfiguration, MeasurementConfigurationAdmin)
admin.site.register(GeoElectricMeasurement, GeoElectricMeasurementAdmin)
admin.site.register(GeoElectricMeasure, GeoElectricMeasureAdmin)
