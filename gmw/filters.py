from django.db.models import JSONField
from django_filters import DateFilter, FilterSet
from django_filters import rest_framework as filters

from api.mixins import DateTimeFilterMixin
from gmn.models import Measuringpoint

from .models import GMW, Event, MonitoringTube


class GmwFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = GMW
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": filters.CharFilter,
                "extra": {"lookup_expr": "icontains"},
            }
        }


class MonitoringTubeFilter(DateTimeFilterMixin, FilterSet):
    gmn_bro_id = filters.CharFilter(
        field_name="gmw__bro_id",  # dummy or related field for validation
        method="filter_by_gmn_bro_id",
        label="GMN BRO ID",
    )
    gmw_bro_id = filters.CharFilter(
        field_name="gmw__bro_id",  # this one actually matches the model
        method="filter_by_gmw_bro_id",
        label="GMW BRO ID",
    )

    class Meta:
        model = MonitoringTube
        exclude = ["geo_ohm_cables"]

    def filter_by_gmn_bro_id(self, queryset, name, value) -> any:
        measuringpoints = Measuringpoint.objects.filter(gmn__bro_id=value)
        gmw_ids = measuringpoints.values_list("gmw_bro_id", flat=True)
        return queryset.filter(gmw__bro_id__in=gmw_ids)

    def filter_by_gmw_bro_id(self, queryset, name, value) -> any:
        return queryset.filter(gmw__bro_id=value)


class EventFilter(DateTimeFilterMixin, FilterSet):
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
