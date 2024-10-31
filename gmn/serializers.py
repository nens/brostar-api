from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from gmw import models as gmw_models

from . import models as gmn_models


class GMNSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = gmn_models.GMN
        fields = "__all__"


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

    def get_gmw_uuid(self, obj: gmw_models.MonitoringTube) -> str | None:
        try:
            return gmw_models.GMW.objects.get(
                bro_id=obj.gmw.bro_id, data_owner=obj.data_owner
            ).uuid
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned:
            return (
                gmw_models.GMW.objects.filter(
                    bro_id=obj.gmw.bro_id, data_owner=obj.data_owner
                )
                .first()
                .uuid
            )

    def get_monitoringtube_uuid(self, obj: gmw_models.MonitoringTube) -> str | None:
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
                    bro_id=obj.gmw.bro_id,
                    tube_number=obj.tube_number,
                    data_owner=obj.data_owner,
                )
                .first()
                .uuid
            )
