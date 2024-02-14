from rest_framework import serializers
from . import models
from .mixins import UrlFieldMixin


class ImportTaskSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.ImportTask
        fields = "__all__"


class UploadTaskSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.UploadTask
        fields = "__all__"
