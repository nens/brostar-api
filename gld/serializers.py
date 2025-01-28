from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from gld.models import GLD, MeasurementTvp, Observation


class GLDSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    nr_of_observations = serializers.SerializerMethodField()

    class Meta:
        model = GLD
        fields = "__all__"

    def get_nr_of_observations(self, obj: GLD) -> int:
        return obj.nr_of_observations


class ObservationSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    nr_of_measurements = serializers.SerializerMethodField()

    class Meta:
        model = Observation
        fields = "__all__"

    def get_nr_of_measurements(self, obj: Observation) -> int:
        return obj.nr_of_measurements


class MeasurementTvpSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = MeasurementTvp
        fields = "__all__"
