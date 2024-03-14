from django.contrib import admin

from . import models as gmw_models

admin.site.register(gmw_models.GMW)
admin.site.register(gmw_models.MonitoringTube)
