from rest_framework import serializers

from api.mixins import UrlFieldMixin

from . import models


class GMNSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.GMN
        fields = "__all__"


class MeasuringpointSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Measuringpoint
        fields = "__all__"
