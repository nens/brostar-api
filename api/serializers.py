from rest_framework import serializers
from . import models
from .mixins import UrlFieldMixin


class ImportTaskSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.ImportTask
        fields = "__all__"
