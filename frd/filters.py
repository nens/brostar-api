from django.db.models import JSONField
from django_filters import CharFilter, FilterSet

from api.mixins import DateTimeFilterMixin

from .models import FRD


class FrdFilter(DateTimeFilterMixin, FilterSet):
    class Meta:
        model = FRD
        fields = "__all__"
        filter_overrides = {
            JSONField: {
                "filter_class": CharFilter,
            },
        }
