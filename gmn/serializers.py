from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin

from . import models as gmn_models


class GMNSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = gmn_models.GMN
        fields = "__all__"


class MeasuringpointSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = gmn_models.Measuringpoint
        fields = "__all__"
