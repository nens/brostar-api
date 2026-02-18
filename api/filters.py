from django_filters import rest_framework as filters

from . import models as api_models


class UploadTaskFilter(filters.FilterSet):
    # Is a subset of metadata (JSON) field
    request_reference__icontains = filters.CharFilter(
        field_name="metadata__requestReference", lookup_expr="icontains"
    )
    bro_id__icontains = filters.CharFilter(field_name="bro_id", lookup_expr="icontains")
    registration_type__icontains = filters.CharFilter(
        field_name="registration_type", lookup_expr="icontains"
    )

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
