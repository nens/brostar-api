"""Shared request fields for all correction endpoints."""

from typing import Any

from rest_framework import serializers

CORRECTION_REASONS = ("eigenCorrectie", "bronhouder", "kwaliteitsregime", "inOnderzoek")
DEFAULT_CORRECTION_REASON = "eigenCorrectie"


def to_snake_case(key: str) -> str:
    return "".join(f"_{char.lower()}" if char.isupper() else char for char in key)


def normalize_keys(data: Any) -> Any:
    """Accept both camelCase and snake_case keys in (nested) request bodies."""
    if isinstance(data, dict):
        return {
            to_snake_case(key): normalize_keys(value) for key, value in data.items()
        }
    if isinstance(data, list):
        return [normalize_keys(item) for item in data]
    return data


class BaseCorrectionSerializer(serializers.Serializer):
    """Fields that every correction request shares."""

    project_number = serializers.CharField()
    correction_reason = serializers.ChoiceField(
        choices=CORRECTION_REASONS, default=DEFAULT_CORRECTION_REASON
    )
    investigator_kvk = serializers.CharField(
        required=False, allow_null=True, allow_blank=False
    )
    use_organisation_kvk = serializers.BooleanField(default=False)

    #: Fields that may not be combined with this request.
    forbidden_fields: tuple[str, ...] = ()

    def to_internal_value(self, data: Any) -> Any:
        return super().to_internal_value(normalize_keys(data))

    def validate_project_number(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError(
                "project_number mag alleen uit cijfers bestaan, bijvoorbeeld '1255'."
            )
        return value

    def validate_investigator_kvk(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError(
                "investigator_kvk mag alleen uit cijfers bestaan."
            )
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        provided = set(normalize_keys(self.initial_data or {}))
        wrong = provided.intersection(self.forbidden_fields)
        if wrong:
            raise serializers.ValidationError(
                f"Deze velden horen niet bij dit endpoint: {', '.join(sorted(wrong))}."
            )
        return attrs
