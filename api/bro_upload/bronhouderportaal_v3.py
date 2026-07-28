import logging

import requests
from django.conf import settings

logger = logging.getLogger(__file__)


def test_oauth2_bronhouderportaal(token_username: str, token_password: str):
    token_url = settings.BRONHOUDERPORTAAL_AUTH_URL
    client_id = "bhp-api-v3-client"
    grant_type = "password"

    data = {
        "grant_type": grant_type,
        "client_id": client_id,
        "username": token_username,
        "password": token_password,
    }

    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        logger.info(f"Access Token: {access_token}")
        logger.info(f"Refresh Token: {refresh_token}")
        return access_token, refresh_token

    else:
        logger.error(
            f"Failed to obtain access token. Status code: {response.status_code}, Response: {response.text}"
        )
        return None


def test_oauth2_machtigingen(access_token: str):
    """Have to use bearer"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    response = requests.get(
        f"{settings.BRONHOUDERPORTAAL_URL}/api/v3/ontvangen-machtigingen",
        headers=headers,
    )
    logger.info(response.json())


def test_oauth2_refresh_token(refresh_token: str):
    token_url = settings.BRONHOUDERPORTAAL_AUTH_URL
    client_id = "bhp-api-v3-client"

    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
    }

    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        new_access_token = token_data.get("access_token")
        new_refresh_token = token_data.get("refresh_token")
        logger.info(f"New Access Token: {new_access_token}")
        logger.info(f"New Refresh Token: {new_refresh_token}")
        return new_access_token, new_refresh_token

    else:
        logger.error(
            f"Failed to refresh access token. Status code: {response.status_code}, Response: {response.text}"
        )
        return None, None
