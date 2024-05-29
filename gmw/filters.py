from django_filters import rest_framework as filters

from .models import MonitoringTube


class MonitoringTubeFilter(filters.FilterSet):
    class Meta:
        model = MonitoringTube
        exclude = ["geo_ohm_cables"]
