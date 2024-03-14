from django_filters import rest_framework as filters

from . import models as api_models


class UploadTaskFilter(filters.FilterSet):
    class Meta:
        model = api_models.UploadTask
        exclude = ["metadata", "sourcedocument_data"]
