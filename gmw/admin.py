from django.contrib import admin

from . import models as gmw_models


class GMWAdmin(admin.ModelAdmin):
    model = gmw_models.GMW
    list_display = (
        "bro_id",
        "data_owner",
    )

    list_filter = ("data_owner",)


class MonitoringTubeAdmin(admin.ModelAdmin):
    model = gmw_models.MonitoringTube
    list_display = (
        "gmw",
        "tube_number",
        "data_owner",
    )

    list_filter = ("data_owner",)


class EventAdmin(admin.ModelAdmin):
    model = gmw_models.Event
    list_display = (
        "gmw",
        "event_name",
        "event_date",
        "data_owner",
    )

    list_filter = (
        "data_owner",
        "event_name",
    )


admin.site.register(gmw_models.GMW, GMWAdmin)
admin.site.register(gmw_models.MonitoringTube, MonitoringTubeAdmin)
admin.site.register(gmw_models.Event, EventAdmin)
