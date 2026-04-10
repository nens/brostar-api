from django.contrib import admin

from . import models

admin.site.register(models.GAR)
admin.site.register(models.FieldSample)
admin.site.register(models.LaboratoryAnalysis)
