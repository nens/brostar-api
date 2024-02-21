from django_filters import rest_framework as filters
from . import models


class UploadTaskFilter(filters.FilterSet):
    class Meta:
        model = models.UploadTask
        exclude = ["metadata", "sourcedocument_data"]
