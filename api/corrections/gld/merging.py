"""Pure merge functions: apply incoming corrections to existing BRO data."""

from dataclasses import replace
from typing import Any

from ..exceptions import CorrectionValidationError
from .matching import parse_time
from .xml_reader import Measurement

PROCEDURE_FIELDS = (
    "process_reference",
    "evaluation_procedure",
    "measurement_instrument_type",
    "air_pressure_compensation_type",
    "validation_status",
    "observation_type",
)


def merge_measurements(
    existing: list[Measurement],
    incoming: list[Measurement],
) -> tuple[list[Measurement], int, list[str]]:
    """Replace matching measurements and add the rest, keeping the order by time.

    Empty measurements (without value and censorReason) are treated as deletion markers
    and are removed from the result without being added to the merge.

    Returns the new series, the number of changed measurements and a log.
    """
    merged = list(existing)

    log: list[str] = []
    changed = 0

    for measurement in incoming:
        normalized_time = parse_time(measurement.time)

        # Build indexes dynamically to handle deletions correctly
        indexes: dict[Any, list[int]] = {}
        for index, m in enumerate(merged):
            indexes.setdefault(parse_time(m.time), []).append(index)

        matches = indexes.get(normalized_time, [])

        if len(matches) > 1:
            matched_times = ", ".join(merged[index].time for index in matches)
            raise CorrectionValidationError(
                f"Meerdere waarden hebben hetzelfde tijdstip als "
                f"{measurement.time}: {matched_times}. Controleer de data."
            )

        # Empty measurements (no value, no censorReason) are deletion markers
        if measurement.value is None and measurement.censor_reason is None:
            if matches:
                index = matches[0]
                removed_time = merged[index].time
                del merged[index]
                changed += 1
                log.append(f"Meting op {removed_time} verwijderd.")
            continue

        index = matches[0] if matches else None

        if index is None:
            merged.append(measurement)
            changed += 1
            log.append(f"Meting toegevoegd op {measurement.time}.")
            continue

        current = merged[index]
        if (
            current.content() == measurement.content()
            and current.time == measurement.time
        ):
            log.append(f"Meting op {measurement.time} was al gelijk; niets gewijzigd.")
            continue

        merged[index] = measurement
        changed += 1
        if current.time == measurement.time:
            log.append(
                f"Meting op {measurement.time} vervangen "
                f"(waarde {current.value} -> {measurement.value})."
            )
        else:
            log.append(
                f"Meting op {current.time} vervangen door {measurement.time} "
                f"(hetzelfde genormaliseerde tijdstip, "
                f"waarde {current.value} -> {measurement.value})."
            )

    merged.sort(key=lambda item: parse_time(item.time))
    return merged, changed, log


def merge_procedure(
    existing: dict[str, Any], updates: dict[str, Any]
) -> tuple[dict[str, Any], int, list[str]]:
    """Apply procedure updates, ignoring fields that are not sent along."""
    merged = dict(existing)
    log: list[str] = []
    changed = 0

    for field_name in PROCEDURE_FIELDS:
        if field_name not in updates:
            continue

        new_value = updates[field_name]
        if merged.get(field_name) == new_value:
            log.append(f"{field_name} was al '{new_value}'; niets gewijzigd.")
            continue

        log.append(f"{field_name}: '{merged.get(field_name)}' -> '{new_value}'.")
        merged[field_name] = new_value
        changed += 1

    return merged, changed, log


def measurement_from_payload(payload: dict[str, Any]) -> Measurement:
    """Build a Measurement from a validated request payload."""
    return replace(
        Measurement(time=payload["time"]),
        value=payload.get("value"),
        status_quality_control=payload.get("status_quality_control") or "onbekend",
        censor_reason=payload.get("censor_reason"),
        censoring_limitvalue=payload.get("censoring_limitvalue"),
    )
