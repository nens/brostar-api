from django.db.models import JSONField
from django_filters import CharFilter, FilterSet
from django_filters import rest_framework as filters

from api.mixins import DateTimeFilterMixin

from .models import (
    GUF,
    DesignInstallation,
    DesignLoop,
    DesignSurfaceInfiltration,
    DesignWell,
    EnergyCharacteristics,
    GUFEvent,
)


class GufFilter(DateTimeFilterMixin, FilterSet):
    bro_id__icontains = filters.CharFilter(field_name="bro_id", lookup_expr="icontains")

    class Meta:
        model = GUF
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }


class DesignInstallationFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = DesignInstallation
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }


class DesignLoopFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = DesignLoop
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }


class DesignWellFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = DesignWell
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }


class DesignSurfaceInfiltrationFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = DesignSurfaceInfiltration
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }


class GUFEventFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = GUFEvent
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }


class EnergyCharacteristicsFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = EnergyCharacteristics
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }
