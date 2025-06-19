from django_filters import DateFilter, FilterSet

from api.mixins import DateTimeFilterMixin

from .models import GMN, IntermediateEvent, Measuringpoint


class GmnFilter(DateTimeFilterMixin, FilterSet):
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


class MeasuringPointFilter(DateTimeFilterMixin, FilterSet):
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


class IntermediateEventFilter(DateTimeFilterMixin, FilterSet):
    measuringpoint_start_date__gt = DateFilter(
        field_name="event_date", lookup_expr="gt"
    )
    measuringpoint_start_date__gte = DateFilter(
        field_name="event_date", lookup_expr="gte"
    )
    measuringpoint_start_date__lt = DateFilter(
        field_name="event_date", lookup_expr="lt"
    )
    measuringpoint_start_date__lte = DateFilter(
        field_name="event_date", lookup_expr="lte"
    )

    class Meta:
        model = IntermediateEvent
        fields = "__all__"
