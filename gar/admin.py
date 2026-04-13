from django.contrib import admin

from . import models

admin.site.register(models.GAR)
admin.site.register(models.FieldMeasurement)
admin.site.register(models.LaboratoryResearch)
admin.site.register(models.AnalysisProcess)
admin.site.register(models.Analysis)
