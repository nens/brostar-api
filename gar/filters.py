from django.db.models import JSONField
from django_filters import CharFilter, FilterSet
from django_filters import rest_framework as filters

from api.mixins import DateTimeFilterMixin

from . import models as gar_models


class GarFilter(DateTimeFilterMixin, FilterSet):
    bro_id__icontains = filters.CharFilter(field_name="bro_id", lookup_expr="icontains")

    class Meta:
        model = gar_models.GAR
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }
