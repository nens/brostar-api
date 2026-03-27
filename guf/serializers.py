from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from guf.models import (
    GUF,
    DesignInstallation,
    DesignLoop,
    DesignSurfaceInfiltration,
    DesignWell,
    EnergyCharacteristics,
    GUFEvent,
)


class GUFSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = GUF
        fields = "__all__"


class GUFIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GUF
        fields = [
            "uuid",
            "bro_id",
            "delivery_accountable_party",
            "data_owner",
        ]


class DesignInstallationSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = DesignInstallation
        fields = "__all__"


class DesignInstallationIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignInstallation
        fields = [
            "uuid",
            "design_installation_id",
            "installation_function",
            "guf",
            "data_owner",
        ]


class EnergyCharacteristicsSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = EnergyCharacteristics
        fields = "__all__"


class DesignLoopSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = DesignLoop
        fields = "__all__"


class DesignLoopIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignLoop
        fields = [
            "uuid",
            "design_loop_id",
            "loop_type",
            "installation",
            "data_owner",
        ]


class DesignWellSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = DesignWell
        fields = "__all__"


class DesignWellIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignWell
        fields = [
            "uuid",
            "design_well_id",
            "height",
            "installation",
            "data_owner",
        ]


class DesignSurfaceInfiltrationSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = DesignSurfaceInfiltration
        fields = "__all__"


class DesignSurfaceInfiltrationIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignSurfaceInfiltration
        fields = [
            "uuid",
            "design_surface_infiltration_id",
            "installation",
            "data_owner",
        ]


class GUFEventSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = GUFEvent
        fields = "__all__"


class GUFEventIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GUFEvent
        fields = [
            "uuid",
            "event_name",
            "event_date",
            "guf",
            "data_owner",
        ]


# Optional nested serializers for detailed responses
class DesignInstallationOverviewSerializer(serializers.ModelSerializer):
    nr_of_loops = serializers.ReadOnlyField()
    nr_of_wells = serializers.ReadOnlyField()
    nr_of_surface_infiltrations = serializers.ReadOnlyField()

    class Meta:
        model = DesignInstallation
        fields = [
            "uuid",
            "design_installation_id",
            "installation_function",
            "design_installation_pos",
            "nr_of_loops",
            "nr_of_wells",
            "nr_of_surface_infiltrations",
        ]


class GUFDetailSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    installations = DesignInstallationOverviewSerializer(many=True, read_only=True)
    nr_of_installations = serializers.ReadOnlyField()
    nr_of_events = serializers.ReadOnlyField()

    class Meta:
        model = GUF
        fields = "__all__"
