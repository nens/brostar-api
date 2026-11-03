import hashlib
import logging
import threading
import time
from dataclasses import dataclass

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

CLIENT_ID = "bhp-api-v3-client"
TOKEN_REQUEST_TIMEOUT = 30


@dataclass
class _CachedToken:
    access_token: str
    refresh_token: str | None
    expires_at: float


_token_cache: dict[str, _CachedToken] = {}
_token_cache_lock = threading.Lock()


def _cache_key(token_url: str, username: str, password: str) -> str:
    credentials = f"{token_url}\0{username}\0{password}".encode()
    return hashlib.sha256(credentials).hexdigest()


def _request_token(data: dict[str, str]) -> _CachedToken:
    response = requests.post(
        settings.BRONHOUDERPORTAAL_AUTH_URL,
        data=data,
        timeout=TOKEN_REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    token_data = response.json()
    if not isinstance(token_data, dict):
        raise ValueError("Bronhouderportaal returned an invalid token response")

    access_token = token_data.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise ValueError("Bronhouderportaal token response has no access_token")

    refresh_token = token_data.get("refresh_token")
    if not isinstance(refresh_token, str):
        refresh_token = None

    try:
        expires_in = float(token_data.get("expires_in", 300))
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Bronhouderportaal returned an invalid token expiry"
        ) from error

    refresh_margin = min(30, expires_in * 0.1)
    expires_at = time.monotonic() + max(0, expires_in - refresh_margin)
    return _CachedToken(access_token, refresh_token, expires_at)


def get_access_token(token_username: str, token_password: str) -> str:
    """Return a cached v3 access token, refreshing or reacquiring it as needed."""
    token_url = settings.BRONHOUDERPORTAAL_AUTH_URL
    cache_key = _cache_key(token_url, token_username, token_password)

    with _token_cache_lock:
        cached_token = _token_cache.get(cache_key)
        if cached_token and cached_token.expires_at > time.monotonic():
            return cached_token.access_token

        if cached_token and cached_token.refresh_token:
            refresh_data = {
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "refresh_token": cached_token.refresh_token,
            }
            try:
                cached_token = _request_token(refresh_data)
            except requests.HTTPError as error:
                if error.response is None or error.response.status_code not in (
                    400,
                    401,
                ):
                    raise
                logger.info(
                    "Bronhouderportaal rejected a refresh token; requesting a new token"
                )
            else:
                _token_cache[cache_key] = cached_token
                return cached_token.access_token

        password_data = {
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "username": token_username,
            "password": token_password,
        }
        cached_token = _request_token(password_data)
        _token_cache[cache_key] = cached_token
        return cached_token.access_token


def get_bearer_headers(token_username: str, token_password: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {get_access_token(token_username, token_password)}"
    }
