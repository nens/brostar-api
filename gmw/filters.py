from typing import Any

from django_filters import DateFilter, FilterSet
from django_filters import rest_framework as filters

from api.mixins import DateTimeFilterMixin
from gmn.models import Measuringpoint

from .models import GMW, Event, MonitoringTube


class GmwFilter(DateTimeFilterMixin, FilterSet):
    bro_id__icontains = filters.CharFilter(field_name="bro_id", lookup_expr="icontains")
    internal_id__icontains = filters.CharFilter(
        field_name="internal_id", lookup_expr="icontains"
    )
    well_code__icontains = filters.CharFilter(
        field_name="well_code", lookup_expr="icontains"
    )
    nitg_code__icontains = filters.CharFilter(
        field_name="nitg_code", lookup_expr="icontains"
    )
    well_construction_date__icontains = filters.CharFilter(
        field_name="well_construction_date", lookup_expr="icontains"
    )

    linked_gmn = filters.CharFilter(method="filter_by_linked_gmn")

    class Meta:
        model = GMW
        fields = "__all__"

    def filter_by_linked_gmn(self, queryset, name, value):
        if value.lower() == "none":
            # Filter for wells with no linked GMN
            return queryset.filter(tubes__measuring_points__gmn__isnull=True).distinct()

        return queryset.filter(tubes__measuring_points__gmn__uuid=value).distinct()


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

    def filter_by_gmn_bro_id(self, queryset, name, value) -> Any:
        measuringpoints = Measuringpoint.objects.filter(gmn__bro_id=value)
        gmw_ids = measuringpoints.values_list("gmw_bro_id", flat=True)
        return queryset.filter(gmw__bro_id__in=gmw_ids)

    def filter_by_gmw_bro_id(self, queryset, name, value) -> Any:
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

    def filter_by_gmw_bro_id(self, queryset, name, value) -> Any:
        return queryset.filter(gmw__bro_id=value)
