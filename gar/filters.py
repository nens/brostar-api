from django.db.models import JSONField
from django_filters import CharFilter, FilterSet

from api.mixins import DateTimeFilterMixin

from . import models as gar_models


class GarFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = gar_models.GAR
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }
