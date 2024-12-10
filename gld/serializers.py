from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from gld.models import GLD, MeasurementTvp, Observation


class GLDSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = GLD
        fields = "__all__"


class ObservationSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = Observation
        fields = "__all__"


class MeasurementTvpSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = MeasurementTvp
        fields = "__all__"
