"""GMN calls to the public BRO uitgifteservice."""

import logging

import requests

from api.corrections.client import DEFAULT_TIMEOUT, base_url
from api.corrections.exceptions import BROUnavailable, ObjectNotFound

logger = logging.getLogger("general")


def fetch_gmn_xml(bro_id: str) -> str:
    """Return the GMN including ended measuring points and replaced tubes.

    The BRO only checks whether ``fullHistory`` is present, not its value.
    """
    url = f"{base_url()}/gm/gmn/v1/objects/{bro_id}"

    try:
        response = requests.get(
            url, params={"fullHistory": "ja"}, timeout=DEFAULT_TIMEOUT
        )
    except requests.RequestException as exc:
        logger.warning("BRO request failed for %s: %s", url, exc)
        raise BROUnavailable(
            f"De publieke BRO-uitgifteservice is niet bereikbaar: {exc}"
        ) from exc

    # The BRO answers an unknown id with 400 and "bestaat niet".
    if response.status_code in (400, 404) and "bestaat niet" in response.text:
        raise ObjectNotFound(f"Meetnet {bro_id} bestaat niet in de BRO.")

    if response.status_code >= 400:
        logger.warning(
            "BRO request to %s returned %s: %s",
            url,
            response.status_code,
            response.text[:500],
        )
        raise BROUnavailable(
            f"De publieke BRO-uitgifteservice gaf status {response.status_code} terug."
        )

    return response.text
