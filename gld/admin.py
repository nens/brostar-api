from django.contrib import admin

from . import models as gld_models


class GLDAdmin(admin.ModelAdmin):
    model = gld_models.GLD
    list_display = (
        "bro_id",
        "data_owner",
    )

    list_filter = ("data_owner",)


class ObservationAdmin(admin.ModelAdmin):
    model = gld_models.Observation
    list_display = (
        "gld",
        "observation_type",
        "begin_position",
        "data_owner",
    )

    list_filter = ("data_owner",)


class MeasurementTvpAdmin(admin.ModelAdmin):
    model = gld_models.MeasurementTvp
    list_display = (
        "observation",
        "data_owner",
    )

    list_filter = ("data_owner",)


admin.site.register(gld_models.GLD, GLDAdmin)
admin.site.register(gld_models.Observation, ObservationAdmin)
admin.site.register(gld_models.MeasurementTvp, MeasurementTvpAdmin)
