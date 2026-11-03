"""Matching of measurement times using normalized datetime values."""

from datetime import datetime
from zoneinfo import ZoneInfo

from ..exceptions import CorrectionValidationError

# The BRO delivers its times in local Dutch time with an explicit offset.
DEFAULT_TIMEZONE = ZoneInfo("Europe/Amsterdam")


def parse_time(value: str | datetime) -> datetime:
    """Parse a BRO time into a timezone aware datetime."""
    if isinstance(value, datetime):
        parsed = value
    else:
        text = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise CorrectionValidationError(
                f"'{value}' is geen geldig tijdstip (verwacht ISO-8601)."
            ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=DEFAULT_TIMEZONE)
    return parsed


def seconds_between(first: str | datetime, second: str | datetime) -> float:
    return abs((parse_time(first) - parse_time(second)).total_seconds())


def find_matches(times: list[str], target: str) -> list[int]:
    """Return indices whose normalized datetimes equal the target."""
    normalized_target = parse_time(target)
    return [
        index
        for index, time in enumerate(times)
        if parse_time(time) == normalized_target
    ]


def single_match(times: list[str], target: str) -> int | None:
    """Return the index of the single match, or None when there is no match."""
    matches = find_matches(times, target)

    if len(matches) > 1:
        matched_times = ", ".join(times[index] for index in matches)
        raise CorrectionValidationError(
            f"Meerdere waarden hebben hetzelfde tijdstip als {target}: "
            f"{matched_times}. Controleer de data."
        )

    return matches[0] if matches else None
