from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.mixins import UrlFieldMixin
from gmn import models as gmn_models

from . import models as gmw_models


class GMWSerializer(UrlFieldMixin, serializers.ModelSerializer):
    linked_gmns = serializers.SerializerMethodField()
    nr_of_monitoring_tubes = serializers.SerializerMethodField()
    nr_of_intermediate_events = serializers.SerializerMethodField()

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

    def get_nr_of_monitoring_tubes(self, obj: gmw_models.GMW) -> int:
        return obj.nr_of_tubes

    def get_nr_of_intermediate_events(self, obj: gmw_models.GMW) -> int:
        return obj.nr_of_intermediate_events


class MonitoringTubeOverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = gmw_models.MonitoringTube
        fields = ["uuid", "tube_number", "tube_status"]


class EventsOverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = gmw_models.Event
        fields = ["uuid", "event_name", "event_date"]


class GMWOverviewSerializer(serializers.ModelSerializer):
    linked_gmns = serializers.SerializerMethodField()
    tubes = MonitoringTubeOverviewSerializer(many=True, read_only=True)
    events = EventsOverviewSerializer(many=True, read_only=True)

    class Meta:
        model = gmw_models.GMW
        fields = [
            "uuid",
            "bro_id",
            "linked_gmns",
            "standardized_location",
            "nitg_code",
            "well_construction_date",
            "quality_regime",
            "removed",
            "tubes",
            "events",
        ]

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


class GMWIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = gmw_models.GMW
        fields = [
            "uuid",
            "bro_id",
            "delivery_accountable_party",
            "data_owner",
        ]


class MonitoringTubeSerializer(UrlFieldMixin, serializers.ModelSerializer):
    gmw_well_code = serializers.SerializerMethodField()
    gmw_bro_id = serializers.SerializerMethodField()
    linked_gmns = serializers.SerializerMethodField()

    class Meta:
        model = gmw_models.MonitoringTube
        fields = "__all__"

    def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

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


class EventSerializer(UrlFieldMixin, serializers.ModelSerializer):
    gmw_well_code = serializers.SerializerMethodField()
    gmw_bro_id = serializers.SerializerMethodField()

    class Meta:
        model = gmw_models.Event
        fields = "__all__"

    def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

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
