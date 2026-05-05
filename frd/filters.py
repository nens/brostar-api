import django_filters
from django import forms
from django.db.models import ForeignKey, JSONField
from django_filters import CharFilter, FilterSet, UUIDFilter
from django_filters import rest_framework as filters

from api.mixins import DateTimeFilterMixin
from gmw.models import MonitoringTube

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
    gmw = django_filters.ModelChoiceFilter(
        queryset=MonitoringTube.objects.all(),
        widget=forms.TextInput(attrs={"placeholder": "Enter GMW ID"}),
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
            ForeignKey: {
                "filter_class": UUIDFilter,
            },
        }


class MeasurementFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = GeoElectricMeasurement
        fields = "__all__"
        filter_overrides = {
            ForeignKey: {
                "filter_class": UUIDFilter,
            },
        }


class GeoElectricMeasureFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = GeoElectricMeasure
        fields = "__all__"
        filter_overrides = {
            ForeignKey: {
                "filter_class": UUIDFilter,
            },
        }
