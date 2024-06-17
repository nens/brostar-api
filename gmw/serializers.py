from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from gmn import models as gmn_models

from . import models as gmw_models


class GMWSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    linked_gmns = serializers.SerializerMethodField()

    class Meta:
        model = gmw_models.GMW
        fields = "__all__"

    def get_linked_gmns(self, obj: gmw_models.GMW) -> list[gmn_models.GMN] | None:
        try:
            linked_gmns = set(
                measuringpoint.gmn.uuid
                for measuringpoint in gmn_models.Measuringpoint.objects.filter(
                    gmw_bro_id=obj.bro_id
                )
            )
            return list(linked_gmns)

        except ObjectDoesNotExist:
            return None


class MonitoringTubeSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    gmw_well_code = serializers.SerializerMethodField()
    gmw_bro_id = serializers.SerializerMethodField()
    linked_gmns = serializers.SerializerMethodField()

    class Meta:
        model = gmw_models.MonitoringTube
        fields = "__all__"

    def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

    def get_gmw_well_code(self, obj: gmw_models.MonitoringTube) -> str | None:
        try:
            return gmw_models.GMW.objects.get(uuid=obj.gmw.uuid).well_code
        except ObjectDoesNotExist:
            return None

    def get_gmw_bro_id(self, obj: gmw_models.MonitoringTube) -> str | None:
        try:
            return gmw_models.GMW.objects.get(uuid=obj.gmw.uuid).bro_id
        except ObjectDoesNotExist:
            return None

    def get_linked_gmns(
        self, obj: gmw_models.MonitoringTube
    ) -> list[gmn_models.GMN] | None:
        try:
            linked_gmns = set(
                measuringpoint.gmn.uuid
                for measuringpoint in gmn_models.Measuringpoint.objects.filter(
                    gmw_bro_id=obj.gmw.bro_id
                )
            )
            return list(linked_gmns)

        except ObjectDoesNotExist:
            return None
