"""Pure merge functions: apply incoming corrections to existing BRO data."""

from dataclasses import replace
from typing import Any

from .matching import parse_time, single_match
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
    delta_t: float = 0,
) -> tuple[list[Measurement], int, list[str]]:
    """Replace matching measurements and add the rest, keeping the order by time.

    Returns the new series, the number of changed measurements and a log.
    """
    merged = list(existing)
    log: list[str] = []
    changed = 0

    for measurement in incoming:
        times = [item.time for item in merged]
        index = single_match(times, measurement.time, delta_t)

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
                f"(binnen delta_t van {delta_t} seconden, "
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
