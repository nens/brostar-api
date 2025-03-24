from django.contrib import admin

from . import models as gmn_models


class GMNAdmin(admin.ModelAdmin):
    model = gmn_models.GMN
    list_display = (
        "bro_id",
        "data_owner",
    )

    list_filter = ("data_owner",)


class MeasuringpointAdmin(admin.ModelAdmin):
    model = gmn_models.Measuringpoint
    list_display = (
        "gmn",
        "gmw_bro_id",
        "tube_number",
        "data_owner",
    )

    list_filter = ("data_owner",)


class IntermediateEventAdmin(admin.ModelAdmin):
    model = gmn_models.IntermediateEvent
    list_display = (
        "gmn",
        "event_type",
        "event_date",
        "data_owner",
    )

    list_filter = (
        "data_owner",
        "event_type",
    )


admin.site.register(gmn_models.GMN, GMNAdmin)
admin.site.register(gmn_models.Measuringpoint, MeasuringpointAdmin)
admin.site.register(gmn_models.IntermediateEvent, IntermediateEventAdmin)
