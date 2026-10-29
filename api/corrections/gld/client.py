"""GLD specific calls to the public BRO uitgifteservice."""

from typing import Any

from ..client import get_json, get_text
from ..exceptions import ObjectNotFound, ObservationNotFound

# Full range: the correction always works on the complete observation.
FULL_RANGE_START = "1900-01-01T00:00:00"
FULL_RANGE_END = "2100-01-01T00:00:00"


def fetch_observation_xml(bro_id: str, observation_id: str) -> str:
    """Return the dispatchDataResponse XML of a single observation."""
    try:
        return get_text(
            f"/gm/gld/v1/objects/{bro_id}/observations/{observation_id}",
            params={
                "startTVPTime": FULL_RANGE_START,
                "endTVPTime": FULL_RANGE_END,
            },
        )
    except ObjectNotFound as exc:
        raise ObservationNotFound(bro_id, observation_id) from exc


def fetch_observation_summaries(bro_id: str) -> list[dict[str, Any]]:
    """Return the summary of all observations within a GLD."""
    summaries = get_json(f"/gm/gld/v1/objects/{bro_id}/observationsSummary")
    if not isinstance(summaries, list):
        return []
    return summaries
