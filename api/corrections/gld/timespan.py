"""Rule 5: handling measurements that fall outside the observation period.

Measurements inside the current period of the observation need no extra checks.
Only when a measurement falls outside of it, the other observations of the GLD
are consulted: the measurement may only be added when no other observation of
the same type lies closer to that moment.
"""

from datetime import datetime, time, timedelta
from typing import Any

from ..exceptions import CorrectionValidationError
from .matching import DEFAULT_TIMEZONE, parse_time
from .xml_reader import Measurement, ParsedObservation

SUMMARY_DATE_FORMAT = "%d-%m-%Y"


def _start_of_day(value: datetime) -> datetime:
    return datetime.combine(value.date(), time.min, tzinfo=DEFAULT_TIMEZONE)


def _end_of_day(value: datetime) -> datetime:
    return _start_of_day(value) + timedelta(days=1) - timedelta(microseconds=1)


def period_bounds(begin: str | None, end: str | None) -> tuple[datetime, datetime]:
    """Return the inclusive period, where a date covers the whole day."""
    if not begin or not end:
        raise CorrectionValidationError(
            "De observatie heeft geen geldige phenomenonTime; corrigeren is niet mogelijk."
        )
    return _start_of_day(parse_time(begin)), _end_of_day(parse_time(end))


def summary_bounds(summary: dict[str, Any]) -> tuple[datetime, datetime] | None:
    """Return the period of an observationsSummary entry (dd-mm-yyyy dates)."""
    try:
        begin = datetime.strptime(summary["startDate"], SUMMARY_DATE_FORMAT)
        end = datetime.strptime(summary["endDate"], SUMMARY_DATE_FORMAT)
    except (KeyError, TypeError, ValueError):
        return None
    return _start_of_day(begin.replace(tzinfo=DEFAULT_TIMEZONE)), _end_of_day(
        end.replace(tzinfo=DEFAULT_TIMEZONE)
    )


def distance_to_period(moment: str, begin: datetime, end: datetime) -> float:
    """Distance in seconds between a moment and a period; 0 when inside."""
    parsed = parse_time(moment)
    if parsed < begin:
        return (begin - parsed).total_seconds()
    if parsed > end:
        return (parsed - end).total_seconds()
    return 0.0


def times_outside_period(
    observation: ParsedObservation, measurements: list[Measurement]
) -> list[Measurement]:
    begin, end = period_bounds(observation.begin_position, observation.end_position)
    return [
        measurement
        for measurement in measurements
        if distance_to_period(measurement.time, begin, end) > 0
    ]


def assert_best_fitting_observation(
    observation: ParsedObservation,
    summaries: list[dict[str, Any]],
    measurement: Measurement,
) -> None:
    """Raise when another observation of the same type fits the moment better."""
    begin, end = period_bounds(observation.begin_position, observation.end_position)
    own_distance = distance_to_period(measurement.time, begin, end)

    for summary in summaries:
        if summary.get("observationId") == observation.observation_id:
            continue
        if summary.get("observationType") != observation.observation_type:
            continue

        bounds = summary_bounds(summary)
        if bounds is None:
            continue

        if distance_to_period(measurement.time, *bounds) < own_distance:
            raise CorrectionValidationError(
                f"De meting op {measurement.time} valt buiten de periode van "
                f"observatie {observation.observation_id} "
                f"({observation.begin_position} t/m {observation.end_position}), en "
                f"observatie {summary.get('observationId')} van hetzelfde type ligt "
                f"dichterbij ({summary.get('startDate')} t/m {summary.get('endDate')}). "
                "Corrigeer die observatie in plaats hiervan."
            )


def recalculate_period(
    measurements: list[Measurement],
) -> tuple[str, str, str | None]:
    """Return (beginPosition, endPosition, resultTime) for a measurement series.

    # CHECK: beginPosition/endPosition are delivered as dates (the BRO uses day
    # precision here) and the resultTime is set to the latest measurement.
    """
    if not measurements:
        raise CorrectionValidationError(
            "Een observatie kan niet zonder metingen worden aangeleverd."
        )

    times = sorted(parse_time(measurement.time) for measurement in measurements)
    begin = times[0].date().isoformat()
    end = times[-1].date().isoformat()
    result_time = times[-1].isoformat(timespec="seconds")

    return begin, end, result_time
