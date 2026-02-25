from uuid import UUID

from rest_framework import serializers

from api.mixins import UrlFieldMixin
from gmn import models as gmn_models

from . import models as gmw_models


class MonitoringTubeOverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = gmw_models.MonitoringTube
        fields = ["uuid", "tube_number", "tube_status"]


class EventsOverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = gmw_models.Event
        fields = ["uuid", "event_name", "event_date"]


class GMWGeoJSONSerializer(serializers.ModelSerializer):
    """GeoJSON serializer for GMW model"""

    linked_gmns = serializers.SerializerMethodField()
    nr_of_monitoring_tubes = serializers.SerializerMethodField()
    tubes = MonitoringTubeOverviewSerializer(many=True, read_only=True)

    class Meta:
        model = gmw_models.GMW
        fields = [
            "uuid",
            "bro_id",
            "linked_gmns",
            "standardized_location",
            "nitg_code",
            "well_construction_date",
            "nr_of_monitoring_tubes",
            "quality_regime",
            "removed",
            "tubes",
        ]

    def get_nr_of_monitoring_tubes(self, obj):
        """Use prefetched tubes to count - no extra query"""
        return len(obj.tubes.all())

    def get_linked_gmns(self, obj):
        """Get all GMNs linked through any tube in this GMW"""
        linked_gmns = set()
        for tube in obj.tubes.all():  # Uses prefetch cache
            for mp in tube.measuring_points.all():  # Uses prefetch cache
                linked_gmns.add(mp.gmn.uuid)
        return [str(uuid) for uuid in linked_gmns]

    @staticmethod
    def parse_coordinates(location_string: str | None) -> tuple[float, float] | None:
        """Parse 'latitude longitude' string to (lon, lat) tuple for GeoJSON"""
        if not location_string:
            return None
        try:
            parts = location_string.strip().split()
            if len(parts) == 2:
                lat, lon = float(parts[0]), float(parts[1])
                return (lon, lat)  # GeoJSON uses [longitude, latitude] order
        except (ValueError, AttributeError):
            return None
        return None

    def to_representation(self, instance):
        """Convert to GeoJSON Feature format"""
        data = super().to_representation(instance)

        # Parse coordinates
        location_string = data.pop("standardized_location", None)
        coordinates = self.parse_coordinates(location_string)

        # Build GeoJSON Feature
        feature = {
            "type": "Feature",
            "id": str(data["uuid"]),  # GeoJSON id field
            "geometry": {
                "type": "Point",
                "coordinates": coordinates if coordinates else None,
            },
            "properties": data,
        }

        return feature


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
        return obj.nr_of_monitoring_tubes

    def get_nr_of_intermediate_events(self, obj: gmw_models.GMW) -> int:
        return obj.nr_of_intermediate_events


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
