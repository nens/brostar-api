"""Thin client around the public BRO 'uitgifteservice'.

Only used for reading; corrections themselves are delivered through the regular
UploadTask flow.
"""

import logging
from typing import Any

import requests
from django.conf import settings

from .exceptions import BROUnavailable, ObjectNotFound

logger = logging.getLogger("general")

DEFAULT_TIMEOUT = 30


def base_url() -> str:
    url = getattr(
        settings, "BRO_UITGIFTE_SERVICE_URL", "https://publiek.broservices.nl"
    )
    return url.rstrip("/")


def _get(path: str, params: dict[str, Any] | None = None) -> requests.Response:
    url = f"{base_url()}/{path.lstrip('/')}"

    try:
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        logger.warning("BRO request failed for %s: %s", url, exc)
        raise BROUnavailable(
            f"De publieke BRO-uitgifteservice is niet bereikbaar: {exc}"
        ) from exc

    if response.status_code == 404:
        raise ObjectNotFound(f"Niet gevonden in de BRO: {url}")

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

    return response


def get_text(path: str, params: dict[str, Any] | None = None) -> str:
    return _get(path, params).text


def get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    response = _get(path, params)
    try:
        return response.json()
    except ValueError as exc:
        raise BROUnavailable(
            "De publieke BRO-uitgifteservice gaf geen geldige JSON terug."
        ) from exc
