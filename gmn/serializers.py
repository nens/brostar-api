from rest_framework import serializers

from api.mixins import UrlFieldMixin

from . import models as gmn_models


class GMNSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = gmn_models.GMN
        fields = "__all__"


class MeasuringpointSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = gmn_models.Measuringpoint
        fields = "__all__"
