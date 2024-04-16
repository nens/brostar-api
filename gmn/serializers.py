from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.mixins import UrlFieldMixin
from gmw import models as gmw_models

from . import models as gmn_models


class GMNSerializer(UrlFieldMixin):
    class Meta:
        model = gmn_models.GMN
        fields = "__all__"


class MeasuringpointSerializer(UrlFieldMixin):
    gmw_uuid = serializers.SerializerMethodField()
    monitoringtube_uuid = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = gmn_models.Measuringpoint
        fields = "__all__"

    def get_location(self, obj: gmw_models.MonitoringTube) -> gmw_models.GMW | None:
        try:
            return gmw_models.GMW.objects.get(
                bro_id=obj.gmw_bro_id
            ).standardized_location
        except ObjectDoesNotExist:
            return None

    def get_gmw_uuid(self, obj: gmw_models.MonitoringTube) -> gmw_models.GMW | None:
        try:
            return gmw_models.GMW.objects.get(bro_id=obj.gmw_bro_id).uuid
        except ObjectDoesNotExist:
            return None

    def get_monitoringtube_uuid(
        self, obj: gmw_models.MonitoringTube
    ) -> gmw_models.GMW | None:
        try:
            gmw_uuid = self.get_gmw_uuid(obj)
            return gmw_models.MonitoringTube.objects.get(
                gmw=gmw_uuid, tube_number=obj.tube_number
            ).uuid
        except ObjectDoesNotExist:
            return None
