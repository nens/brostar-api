from django_filters import rest_framework as filters

from gmn.models import Measuringpoint

from .models import Event, MonitoringTube


class MonitoringTubeFilter(filters.FilterSet):
    gmn_bro_id = filters.CharFilter(method="filter_by_gmn_bro_id")
    gmw_bro_id = filters.CharFilter(method="filter_by_gmw_bro_id")

    class Meta:
        model = MonitoringTube
        exclude = ["geo_ohm_cables"]

    def filter_by_gmn_bro_id(self, queryset, name, value) -> any:
        measuringpoints = Measuringpoint.objects.filter(gmn__bro_id=value)
        gmw_ids = measuringpoints.values_list("gmw_bro_id", flat=True)
        return queryset.filter(gmw__bro_id__in=gmw_ids)

    def filter_by_gmw_bro_id(self, queryset, name, value) -> any:
        return queryset.filter(gmw__bro_id=value)


class EventFilter(filters.FilterSet):
    gmw_bro_id = filters.CharFilter(method="filter_by_gmw_bro_id")

    class Meta:
        model = Event
        exclude = ["metadata", "sourcedocument_data"]

    def filter_by_gmw_bro_id(self, queryset, name, value) -> any:
        return queryset.filter(gmw__bro_id=value)
