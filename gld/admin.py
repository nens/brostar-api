from django.contrib import admin

from .models import GLD, MeasurementTvp, Observation

admin.site.register(GLD)
admin.site.register(Observation)
admin.site.register(MeasurementTvp)
