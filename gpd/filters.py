from django.db.models import JSONField
from django_filters import CharFilter, FilterSet
from django_filters import rest_framework as filters

from api.mixins import DateTimeFilterMixin

from .models import GPD, Report, VolumeSeries


class GpdFilter(DateTimeFilterMixin, FilterSet):
    bro_id__icontains = filters.CharFilter(field_name="bro_id", lookup_expr="icontains")

    class Meta:
        model = GPD
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }


class ReportFilter(DateTimeFilterMixin, FilterSet):
    report_id__icontains = filters.CharFilter(
        field_name="report_id", lookup_expr="icontains"
    )

    class Meta:
        model = Report
        fields = "__all__"


class VolumeSeriesFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = VolumeSeries
        fields = "__all__"
