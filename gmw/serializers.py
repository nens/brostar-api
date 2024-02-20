from rest_framework import serializers
from . import models
from api.mixins import UrlFieldMixin


class GMWSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.GMW
        fields = "__all__"


class MonitoringTubeSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.MonitoringTube
        fields = "__all__"
