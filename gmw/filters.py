from django_filters import DateFilter
from django_filters import rest_framework as filters

from api.mixins import DateTimeFilterMixin
from gmn.models import Measuringpoint

from .models import GMW, Event, MonitoringTube


class GmwFilter(DateTimeFilterMixin):
    class Meta:
        model = GMW
        fields = "__all__"


class MonitoringTubeFilter(DateTimeFilterMixin):
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


class EventFilter(DateTimeFilterMixin):
    gmw_bro_id = filters.CharFilter(method="filter_by_gmw_bro_id")
    event_date__gt = DateFilter(field_name="event_date", lookup_expr="gt")
    event_date__gte = DateFilter(field_name="event_date", lookup_expr="gte")
    event_date__lt = DateFilter(field_name="event_date", lookup_expr="lt")
    event_date__lte = DateFilter(field_name="event_date", lookup_expr="lte")

    class Meta:
        model = Event
        exclude = ["metadata", "sourcedocument_data"]

    def filter_by_gmw_bro_id(self, queryset, name, value) -> any:
        return queryset.filter(gmw__bro_id=value)
