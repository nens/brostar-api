from django.contrib import admin

from . import models


class GARAdmin(admin.ModelAdmin):
    model = models.GAR
    list_display = (
        "bro_id",
        "data_owner",
    )

    list_filter = (
        "data_owner",
        "bro_id",
    )


class FieldMeasurementAdmin(admin.ModelAdmin):
    model = models.FieldMeasurement
    list_display = (
        "gar",
        "parameter",
        "data_owner",
    )

    list_filter = (
        "data_owner",
        "gar",
    )


class LaboratoryResearchAdmin(admin.ModelAdmin):
    model = models.LaboratoryResearch
    list_display = (
        "gar",
        "data_owner",
    )

    list_filter = (
        "data_owner",
        "gar",
    )


class AnalysisProcessAdmin(admin.ModelAdmin):
    model = models.AnalysisProcess
    list_display = (
        "laboratory_research",
        "analyses_date",
        "data_owner",
    )

    list_filter = (
        "data_owner",
        "laboratory_research",
    )


class AnalysisAdmin(admin.ModelAdmin):
    model = models.Analysis
    list_display = (
        "analysis_process",
        "parameter",
        "data_owner",
    )

    list_filter = (
        "data_owner",
        "analysis_process",
    )


admin.site.register(models.GAR, GARAdmin)
admin.site.register(models.FieldMeasurement, FieldMeasurementAdmin)
admin.site.register(models.LaboratoryResearch, LaboratoryResearchAdmin)
admin.site.register(models.AnalysisProcess, AnalysisProcessAdmin)
admin.site.register(models.Analysis, AnalysisAdmin)
