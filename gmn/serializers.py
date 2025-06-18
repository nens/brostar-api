from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from gmw import models as gmw_models

from . import models as gmn_models


class GMNSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = gmn_models.GMN
        fields = "__all__"


class MeasuringPointOverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = gmn_models.Measuringpoint
        fields = [
            "uuid",
            "event_type",
            "gmw_bro_id",
            "tube_number",
            "tube_start_date",
            "tube_end_date",
        ]


class GMNOverviewSerializer(serializers.ModelSerializer):
    measuring_points = MeasuringPointOverviewSerializer(many=True, read_only=True)

    class Meta:
        model = gmn_models.GMN
        fields = [
            "uuid",
            "bro_id",
            "name",
            "quality_regime",
            "measuring_points",
        ]


class MeasuringpointSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    gmw_uuid = serializers.SerializerMethodField()
    monitoringtube_uuid = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = gmn_models.Measuringpoint
        fields = "__all__"

    def get_location(self, obj: gmn_models.Measuringpoint) -> str | None:
        try:
            return gmw_models.GMW.objects.get(
                bro_id=obj.gmw_bro_id, data_owner=obj.data_owner
            ).standardized_location
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned:
            return (
                gmw_models.GMW.objects.filter(
                    bro_id=obj.gmw_bro_id, data_owner=obj.data_owner
                )
                .first()
                .standardized_location
            )

    def get_gmw_uuid(self, obj: gmn_models.Measuringpoint) -> str | None:
        try:
            return gmw_models.GMW.objects.get(
                bro_id=obj.gmw_bro_id, data_owner=obj.data_owner
            ).uuid
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned:
            return (
                gmw_models.GMW.objects.filter(
                    bro_id=obj.gmw_bro_id, data_owner=obj.data_owner
                )
                .first()
                .uuid
            )

    def get_monitoringtube_uuid(self, obj: gmn_models.Measuringpoint) -> str | None:
        try:
            gmw_uuid = self.get_gmw_uuid(obj)
            return gmw_models.MonitoringTube.objects.get(
                gmw=gmw_uuid,
                tube_number=obj.tube_number,
                data_owner=obj.data_owner,
            ).uuid
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned:
            return (
                gmw_models.MonitoringTube.objects.filter(
                    gmw=gmw_uuid,
                    tube_number=obj.tube_number,
                    data_owner=obj.data_owner,
                )
                .first()
                .uuid
            )


class GMNIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = gmn_models.GMN
        fields = [
            "uuid",
            "bro_id",
            "delivery_accountable_party",
            "data_owner",
        ]


class IntermediateEventSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = gmn_models.IntermediateEvent
        fields = "__all__"
