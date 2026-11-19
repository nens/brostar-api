"""Request serializers for the GLD correction endpoints."""

import copy
from typing import Any

from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from api.bro_upload.upload_datamodels import GLDAddition, UploadTaskMetadata
from api.corrections.gld.validation import AVAILABLE_RULES

from ..serializers import BaseCorrectionSerializer, normalize_keys

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
        # Allow measurements with value (measurement) or censor_reason (censored).
        # Empty measurements (no value, no censor_reason) are used to delete
        # measurements from the BRO and will be filtered during merging.
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


class GLDValidationOptionsSerializer(serializers.Serializer):
    rules = serializers.ListField(
        child=serializers.ChoiceField(choices=AVAILABLE_RULES),
        required=False,
        allow_empty=True,
    )
    flatline_sigma_multiplier = serializers.FloatField(required=False, min_value=0)
    spike_sigma_multiplier = serializers.FloatField(required=False, min_value=0)
    tube_top_tolerance = serializers.FloatField(required=False, min_value=0)
    tube_bottom_tolerance = serializers.FloatField(required=False, min_value=0)
    sensor_height_tolerance = serializers.FloatField(required=False, min_value=0)
    sensor_height = serializers.FloatField(required=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        rules = attrs.get("rules")
        if rules and "at_or_below_sensor_height" in rules:
            if "sensor_height" not in attrs:
                raise serializers.ValidationError(
                    {"sensor_height": "This field is required for this rule."}
                )
        return attrs


class GLDRegistrationSerializer(serializers.Serializer):
    """Request body for creating one or more GLD_Addition UploadTasks."""

    project_number = serializers.CharField()
    metadata = serializers.JSONField()
    sourcedocument_data = serializers.JSONField()
    validation_options = GLDValidationOptionsSerializer(required=False)

    GENERATED_ID_FIELDS = {
        "observation_id",
        "observation_process_id",
        "measurement_timeseries_id",
    }
    metadata_model: UploadTaskMetadata
    addition_model: GLDAddition

    def to_internal_value(self, data: Any) -> Any:
        return super().to_internal_value(normalize_keys(data))

    def validate_project_number(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError(
                "project_number mag alleen uit cijfers bestaan, bijvoorbeeld '1255'."
            )
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request_data = normalize_keys(self.initial_data or {})
        provided_source = attrs.get("sourcedocument_data")
        if not isinstance(provided_source, dict):
            raise serializers.ValidationError(
                {"sourcedocument_data": "Expected an object."}
            )

        included_ids = self.GENERATED_ID_FIELDS.intersection(
            set(provided_source) | set(request_data)
        )
        if included_ids:
            raise serializers.ValidationError(
                {
                    "sourcedocument_data": (
                        "These identifiers are generated by the server and must not "
                        f"be supplied: {', '.join(sorted(included_ids))}."
                    )
                }
            )

        try:
            self.metadata_model = UploadTaskMetadata(**attrs["metadata"])
        except PydanticValidationError as exc:
            raise serializers.ValidationError({"metadata": str(exc)}) from exc

        try:
            self.addition_model = GLDAddition(
                **copy.deepcopy(attrs["sourcedocument_data"])
            )
        except PydanticValidationError as exc:
            raise serializers.ValidationError(
                {"sourcedocument_data": str(exc)}
            ) from exc

        if not self.addition_model.time_value_pairs:
            raise serializers.ValidationError(
                {"sourcedocument_data": "At least one measurement is required."}
            )
        return attrs
