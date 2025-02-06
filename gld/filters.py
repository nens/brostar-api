import datetime

from django_filters import DateFilter
from django_filters import rest_framework as filters

from api.mixins import DateTimeFilterMixin

from . import models as gld_models


class DateTimeStringFilter(filters.Filter):
    def filter(self, qs, value):
        if value in (None, ""):
            return qs
        try:
            # Ensure the value is in the correct format
            datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            return qs.filter(**{self.field_name: value})
        except ValueError:
            return qs.none()


class GldFilter(filters.FilterSet, DateTimeFilterMixin):
    research_first_date__gt = DateFilter(
        field_name="research_first_date", lookup_expr="gt"
    )
    research_first_date__gte = DateFilter(
        field_name="research_first_date", lookup_expr="gte"
    )
    research_first_date__lt = DateFilter(
        field_name="research_first_date", lookup_expr="lt"
    )
    research_first_date__lte = DateFilter(
        field_name="research_first_date", lookup_expr="lte"
    )

    class Meta:
        model = gld_models.GLD
        exclude = ["linked_gmns"]


class ObservationFilter(filters.FilterSet, DateTimeFilterMixin):
    begin_position__gt = DateFilter(field_name="begin_position", lookup_expr="gt")
    begin_position__gte = DateFilter(field_name="begin_position", lookup_expr="gte")
    begin_position__lt = DateFilter(field_name="begin_position", lookup_expr="lt")
    begin_position__lte = DateFilter(field_name="begin_position", lookup_expr="lte")

    class Meta:
        model = gld_models.Observation
        fields = "__all__"


class MeasurementTvpFilter(filters.FilterSet, DateTimeFilterMixin):
    time = DateTimeStringFilter(field_name="time")

    class Meta:
        model = gld_models.MeasurementTvp
        fields = "__all__"
