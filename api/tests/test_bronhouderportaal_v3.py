from types import SimpleNamespace
from unittest import mock

import pytest
import requests
from django.conf import settings

from api.bro_import import object_import
from api.bro_upload import bronhouderportaal_v3


@pytest.fixture(autouse=True)
def clear_token_cache():
    bronhouderportaal_v3._token_cache.clear()
    yield
    bronhouderportaal_v3._token_cache.clear()


def _token_response(access_token, refresh_token=None, expires_in=3600):
    response = mock.Mock()
    response.json.return_value = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
    }
    return response


def test_get_access_token_uses_password_grant_and_caches_token():
    with mock.patch(
        "api.bro_upload.bronhouderportaal_v3.requests.post",
        return_value=_token_response("access-token", "refresh-token"),
    ) as mock_post:
        token = bronhouderportaal_v3.get_access_token("token-user", "token-password")
        cached_token = bronhouderportaal_v3.get_access_token(
            "token-user", "token-password"
        )

    assert token == cached_token == "access-token"
    mock_post.assert_called_once_with(
        settings.BRONHOUDERPORTAAL_AUTH_URL,
        data={
            "grant_type": "password",
            "client_id": "bhp-api-v3-client",
            "username": "token-user",
            "password": "token-password",
        },
        timeout=30,
    )


def test_get_access_token_refreshes_expired_token():
    with mock.patch(
        "api.bro_upload.bronhouderportaal_v3.requests.post",
        side_effect=[
            _token_response("expired-access-token", "refresh-token", expires_in=0),
            _token_response("new-access-token", "new-refresh-token"),
        ],
    ) as mock_post:
        initial_token = bronhouderportaal_v3.get_access_token(
            "token-user", "token-password"
        )
        refreshed_token = bronhouderportaal_v3.get_access_token(
            "token-user", "token-password"
        )

    assert initial_token == "expired-access-token"
    assert refreshed_token == "new-access-token"
    assert mock_post.call_count == 2
    assert mock_post.call_args.kwargs["data"] == {
        "grant_type": "refresh_token",
        "client_id": "bhp-api-v3-client",
        "refresh_token": "refresh-token",
    }


def test_get_access_token_surfaces_token_endpoint_errors():
    response = mock.Mock()
    response.status_code = 401
    response.raise_for_status.side_effect = requests.HTTPError(
        "Unauthorized", response=response
    )
    with (
        mock.patch(
            "api.bro_upload.bronhouderportaal_v3.requests.post",
            return_value=response,
        ),
        pytest.raises(requests.HTTPError),
    ):
        bronhouderportaal_v3.get_access_token("token-user", "token-password")


def test_gmw_importer_uses_bearer_auth_for_bronhouderportaal():
    importer = object_import.GMWObjectImporter(
        bro_id="GMW000000068159",
        data_owner=SimpleNamespace(
            bro_user_token="token-user", bro_user_password="token-password"
        ),
    )
    mock_response = mock.Mock()
    mock_response.raise_for_status = mock.Mock()
    mock_response.content = b'{"transacties":[]}'
    mock_response.json.return_value = {
        "transacties": [{"objectIdBronhouder": "internal-id"}]
    }

    with (
        mock.patch.object(importer.s, "get", return_value=mock_response) as mock_get,
        mock.patch(
            "api.bro_import.object_import.get_bearer_headers",
            return_value={"Authorization": "Bearer test-access-token"},
        ),
    ):
        internal_id = importer.retrieve_internal_id("GMW000000068159")

    assert internal_id == "internal-id"
    assert mock_get.call_args.kwargs["headers"] == {
        "Authorization": "Bearer test-access-token"
    }
