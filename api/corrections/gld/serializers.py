"""Request serializers for the GLD correction endpoints."""

from typing import Any

from rest_framework import serializers

from ..serializers import BaseCorrectionSerializer

OBSERVATION_TYPES = ("reguliereMeting", "controlemeting")
VALIDATION_STATUSES = ("onbekend", "voorlopig", "volledigBeoordeeld")
CENSOR_REASONS = ("kleinerDanLimietwaarde", "groterDanLimietwaarde", "onbekend")


class MeasurementSerializer(serializers.Serializer):
    time = serializers.CharField()
    value = serializers.FloatField(required=False, allow_null=True)
    status_quality_control = serializers.CharField(required=False, allow_null=True)
    censor_reason = serializers.ChoiceField(
        choices=CENSOR_REASONS, required=False, allow_null=True
    )
    censoring_limitvalue = serializers.FloatField(required=False, allow_null=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if attrs.get("value") is None and not attrs.get("censor_reason"):
            raise serializers.ValidationError(
                "Een meting zonder 'value' moet een 'censor_reason' hebben."
            )
        return attrs


class ProcedureSerializer(serializers.Serializer):
    process_reference = serializers.CharField(required=False)
    evaluation_procedure = serializers.CharField(required=False)
    measurement_instrument_type = serializers.CharField(required=False)
    air_pressure_compensation_type = serializers.CharField(
        required=False, allow_null=True
    )
    validation_status = serializers.ChoiceField(
        choices=VALIDATION_STATUSES, required=False
    )
    observation_type = serializers.ChoiceField(
        choices=OBSERVATION_TYPES, required=False
    )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not attrs:
            raise serializers.ValidationError(
                "Geef minimaal één procedureveld op om te corrigeren."
            )
        return attrs


class GLDMeasurementCorrectionSerializer(BaseCorrectionSerializer):
    forbidden_fields = ("procedure",)

    measurements = serializers.ListField(
        child=MeasurementSerializer(), allow_empty=False
    )


class GLDProcedureCorrectionSerializer(BaseCorrectionSerializer):
    forbidden_fields = ("measurements",)

    procedure = ProcedureSerializer()
