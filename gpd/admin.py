from django.contrib import admin

from .models import GPD, Report


class GPDAdmin(admin.ModelAdmin):
    model = GPD
    list_display = (
        "bro_id",
        "data_owner",
    )

    list_filter = ("data_owner",)


class ReportAdmin(admin.ModelAdmin):
    model = Report
    list_display = (
        "report_id",
        "data_owner",
    )

    list_filter = ("data_owner",)


admin.site.register(GPD, GPDAdmin)
admin.site.register(Report, ReportAdmin)
