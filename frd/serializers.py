from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from frd.models import (
    FRD,
    GeoElectricMeasure,
    GeoElectricMeasurement,
    MeasurementConfiguration,
)


class FRDSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = FRD
        fields = "__all__"


class FRDIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FRD
        fields = [
            "uuid",
            "bro_id",
            "delivery_accountable_party",
            "data_owner",
        ]


class MeasurementConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementConfiguration
        fields = "__all__"


class GeoElectricMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoElectricMeasurement
        fields = "__all__"


class GeoElectricMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoElectricMeasure
        fields = "__all__"
