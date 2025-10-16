from django_filters import rest_framework as filters

from . import models as api_models


class UploadTaskFilter(filters.FilterSet):
    created__lt = filters.IsoDateTimeFilter(field_name="created", lookup_expr="lt")
    created__lte = filters.IsoDateTimeFilter(field_name="created", lookup_expr="lte")
    created__gt = filters.IsoDateTimeFilter(field_name="created", lookup_expr="gt")
    created__gte = filters.IsoDateTimeFilter(field_name="created", lookup_expr="gte")

    updated__lt = filters.IsoDateTimeFilter(field_name="updated", lookup_expr="lt")
    updated__lte = filters.IsoDateTimeFilter(field_name="updated", lookup_expr="lte")
    updated__gt = filters.IsoDateTimeFilter(field_name="updated", lookup_expr="gt")
    updated__gte = filters.IsoDateTimeFilter(field_name="updated", lookup_expr="gte")

    class Meta:
        model = api_models.UploadTask
        exclude = ["metadata", "sourcedocument_data"]
