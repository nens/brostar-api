from rest_framework import serializers

from api.mixins import UrlFieldMixin

from . import models as gmw_models


class GMWSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = gmw_models.GMW
        fields = "__all__"


class MonitoringTubeSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = gmw_models.MonitoringTube
        fields = "__all__"
