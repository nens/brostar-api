from django.contrib import admin

from . import models as gmn_models

admin.site.register(gmn_models.GMN)
admin.site.register(gmn_models.Measuringpoint)
