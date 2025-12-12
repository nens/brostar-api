from uuid import UUID

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

    def get_linked_gmns(self, obj: gmw_models.GMW) -> list[UUID]:
        linked_gmns = set(
            measuringpoint.gmn.uuid
            for measuringpoint in gmn_models.Measuringpoint.objects.filter(
                gmw_bro_id=obj.bro_id
            )
        )
        return list(linked_gmns)

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

    def get_linked_gmns(self, obj: gmw_models.GMW) -> list[UUID]:
        linked_gmns = set(
            measuringpoint.gmn.uuid
            for measuringpoint in gmn_models.Measuringpoint.objects.filter(
                gmw_bro_id=obj.bro_id
            )
        )
        return list(linked_gmns)


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

    def get_gmw_well_code(self, obj: gmw_models.MonitoringTube) -> str | None:
        return obj.gmw.well_code

    def get_gmw_bro_id(self, obj: gmw_models.MonitoringTube) -> str | None:
        return obj.gmw.bro_id

    def get_linked_gmns(self, obj: gmw_models.MonitoringTube) -> list[UUID]:
        linked_gmns = set(
            measuringpoint.gmn.uuid
            for measuringpoint in gmn_models.Measuringpoint.objects.filter(
                gmw_bro_id=obj.gmw.bro_id,
                tube_number=obj.tube_number,
            )
        )
        return list(linked_gmns)


class EventSerializer(UrlFieldMixin, serializers.ModelSerializer):
    gmw_well_code = serializers.SerializerMethodField()
    gmw_bro_id = serializers.SerializerMethodField()

    class Meta:
        model = gmw_models.Event
        fields = "__all__"

    def get_gmw_well_code(self, obj: gmw_models.Event) -> str | None:
        return obj.gmw.well_code

    def get_gmw_bro_id(self, obj: gmw_models.Event) -> str | None:
        return obj.gmw.bro_id
