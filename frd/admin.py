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

    list_filter = (
        "data_owner",
        "bro_id",
    )


class MeasurementConfigurationAdmin(admin.ModelAdmin):
    model = MeasurementConfiguration
    list_display = (
        "frd",
        "data_owner",
    )

    list_filter = (
        "data_owner",
        "frd",
    )


class GeoElectricMeasurementAdmin(admin.ModelAdmin):
    model = GeoElectricMeasurement
    list_display = (
        "frd",
        "measurement_date",
        "data_owner",
    )

    list_filter = (
        "data_owner",
        "frd",
    )


class GeoElectricMeasureAdmin(admin.ModelAdmin):
    model = GeoElectricMeasure
    list_display = (
        "geo_electric_measurement",
        "resistance_value",
        "data_owner",
    )

    list_filter = (
        "data_owner",
        "geo_electric_measurement",
    )


admin.site.register(FRD)
admin.site.register(MeasurementConfiguration)
admin.site.register(GeoElectricMeasurement)
admin.site.register(GeoElectricMeasure)
