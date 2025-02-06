from django_filters import DateFilter
from django_filters import rest_framework as filters

from api.mixins import DateTimeFilterMixin

from .models import GMN, Measuringpoint


class GmnFilter(filters.FilterSet, DateTimeFilterMixin):
    start_date_monitoring__gt = DateFilter(
        field_name="start_date_monitoring", lookup_expr="gt"
    )
    start_date_monitoring__gte = DateFilter(
        field_name="start_date_monitoring", lookup_expr="gte"
    )
    start_date_monitoring__lt = DateFilter(
        field_name="start_date_monitoring", lookup_expr="lt"
    )
    start_date_monitoring__lte = DateFilter(
        field_name="start_date_monitoring", lookup_expr="lte"
    )

    class Meta:
        model = GMN
        fields = "__all__"


class MeasuringPointFilter(filters.FilterSet, DateTimeFilterMixin):
    measuringpoint_start_date__gt = DateFilter(
        field_name="measuringpoint_start_date", lookup_expr="gt"
    )
    measuringpoint_start_date__gte = DateFilter(
        field_name="measuringpoint_start_date", lookup_expr="gte"
    )
    measuringpoint_start_date__lt = DateFilter(
        field_name="measuringpoint_start_date", lookup_expr="lt"
    )
    measuringpoint_start_date__lte = DateFilter(
        field_name="measuringpoint_start_date", lookup_expr="lte"
    )

    class Meta:
        model = Measuringpoint
        fields = "__all__"
