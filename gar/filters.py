from django.db.models import ForeignKey, JSONField
from django_filters import CharFilter, FilterSet, UUIDFilter
from django_filters import rest_framework as filters

from api.mixins import DateTimeFilterMixin

from . import models as gar_models


class GarFilter(DateTimeFilterMixin, FilterSet):
    bro_id__icontains = filters.CharFilter(field_name="bro_id", lookup_expr="icontains")
    gmw_bro_id__icontains = filters.CharFilter(
        field_name="gmw_bro_id", lookup_expr="icontains"
    )

    class Meta:
        model = gar_models.GAR
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
            ForeignKey: {
                "filter_class": UUIDFilter,
            },
        }


class FieldMeasurementFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = gar_models.FieldMeasurement
        fields = "__all__"
        filter_overrides = {
            ForeignKey: {
                "filter_class": UUIDFilter,
            },
        }


class LaboratoryResearchFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = gar_models.LaboratoryResearch
        fields = "__all__"
        filter_overrides = {
            ForeignKey: {
                "filter_class": UUIDFilter,
            },
        }


class AnalysisProcessFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = gar_models.AnalysisProcess
        fields = "__all__"
        filter_overrides = {
            ForeignKey: {
                "filter_class": UUIDFilter,
            },
        }


class AnalysisFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = gar_models.Analysis
        fields = "__all__"
        filter_overrides = {
            ForeignKey: {
                "filter_class": UUIDFilter,
            },
        }
