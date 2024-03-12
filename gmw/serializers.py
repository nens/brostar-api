from rest_framework import serializers

from api.mixins import UrlFieldMixin

from . import models


class GMWSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.GMW
        fields = "__all__"


class MonitoringTubeSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.MonitoringTube
        fields = "__all__"
