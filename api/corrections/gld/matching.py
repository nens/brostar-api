"""Matching of measurement times, with an optional tolerance (delta_t)."""

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


def find_matches(times: list[str], target: str, delta_t: float = 0) -> list[int]:
    """Return the indices of *times* that match *target*, closest match first.

    With ``delta_t <= 0`` only an exact match (same moment in time) counts.
    """
    matches: list[tuple[float, int]] = []
    for index, time in enumerate(times):
        difference = seconds_between(time, target)
        if difference == 0 or (delta_t > 0 and difference <= delta_t):
            matches.append((difference, index))

    matches.sort()
    return [index for _, index in matches]


def single_match(times: list[str], target: str, delta_t: float = 0) -> int | None:
    """Return the index of the single match, or None when there is no match."""
    matches = find_matches(times, target, delta_t)

    if len(matches) > 1:
        matched_times = ", ".join(times[index] for index in matches)
        raise CorrectionValidationError(
            f"Meerdere waarden matchen binnen de opgegeven delta_t ({delta_t} "
            f"seconden) met {target}: {matched_times}. Controleer de data of "
            "kies een kleinere delta_t (seconden)."
        )

    return matches[0] if matches else None
