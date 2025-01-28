from django_filters import rest_framework as filters

from . import models as gld_models


class GldFilter(filters.FilterSet):
    class Meta:
        model = gld_models.GLD
        exclude = ["linked_gmns"]
