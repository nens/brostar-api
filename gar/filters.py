from django.db.models import JSONField
from django_filters import CharFilter, FilterSet
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
        }


class FieldMeasurementFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = gar_models.FieldMeasurement
        fields = "__all__"


class LaboratoryResearchFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = gar_models.LaboratoryResearch
        fields = "__all__"


class AnalysisProcessFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = gar_models.AnalysisProcess
        fields = "__all__"


class AnalysisFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = gar_models.Analysis
        fields = "__all__"
