from django.db.models import JSONField
from django_filters import CharFilter, FilterSet
from django_filters import rest_framework as filters

from api.mixins import DateTimeFilterMixin

from .models import (
    FRD,
    GeoElectricMeasure,
    GeoElectricMeasurement,
    MeasurementConfiguration,
)


class FrdFilter(DateTimeFilterMixin, FilterSet):
    bro_id__icontains = filters.CharFilter(field_name="bro_id", lookup_expr="icontains")
    gmw_bro_id__icontains = filters.CharFilter(
        field_name="gmw_bro_id", lookup_expr="icontains"
    )

    class Meta:
        model = FRD
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }


class MeasurementConfigurationFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = MeasurementConfiguration
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }


class MeasurementFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = GeoElectricMeasurement
        fields = "__all__"


class GeoElectricMeasureFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = GeoElectricMeasure
        fields = "__all__"
