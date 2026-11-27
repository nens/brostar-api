from datetime import date
from typing import Any
from zoneinfo import ZoneInfo

from django.utils import timezone
from rest_framework import serializers

from api.corrections.serializers import normalize_keys


def today_nl() -> date:
    # settings.TIME_ZONE is UTC: just after midnight that is still yesterday.
    return timezone.localdate(timezone=ZoneInfo("Europe/Amsterdam"))


class ComparisonMeasuringPointSerializer(serializers.Serializer):
    measuring_point_code = serializers.CharField(max_length=40)
    bro_id = serializers.RegexField(
        r"^GMW\d{12}$",
        default=None,
        allow_null=True,
        error_messages={"invalid": "Geen geldig GMW-ID, bijvoorbeeld GMW000000083218."},
    )
    tube_number = serializers.IntegerField(min_value=1, default=None, allow_null=True)
    event_date = serializers.DateField(default=None, allow_null=True)
    end_date = serializers.DateField(default=None, allow_null=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        code = attrs["measuring_point_code"]
        has_tube_part = attrs["bro_id"] is not None or attrs["tube_number"] is not None
        if attrs["end_date"]:
            if has_tube_part or attrs["event_date"]:
                raise serializers.ValidationError(
                    f"{code}: geef óf bro_id en tube_number, óf alleen end_date."
                )
        elif attrs["bro_id"] is None or attrs["tube_number"] is None:
            raise serializers.ValidationError(
                f"{code}: bro_id en tube_number zijn verplicht, "
                "of geef end_date om het meetpunt te beëindigen."
            )
        return attrs


class GMNComparisonSerializer(serializers.Serializer):
    project_number = serializers.CharField()
    event_date = serializers.DateField(default=today_nl)
    confirm = serializers.BooleanField(default=False)
    measuring_points = ComparisonMeasuringPointSerializer(many=True, allow_empty=True)

    def to_internal_value(self, data: Any) -> Any:
        return super().to_internal_value(normalize_keys(data))

    def validate_project_number(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError(
                "project_number mag alleen uit cijfers bestaan, bijvoorbeeld '1255'."
            )
        return value
