from unittest import mock

import pytest
import requests

from api.bro_upload.utils import (
    add_xml_to_upload,
    check_delivery_status,
    create_delivery,
    create_upload_url,
    include_delivery_responsible_party,
    simplify_validation_errors,
    validate_xml_file,
)
from api.models import Organisation


# Test simplify_validation_errors function
def test_simplify_validation_errors():
    errors = [
        {
            "loc": ("recursive_model", "lng"),
            "msg": "Field1 is required",
            "type": "value_error.missing",
        },
        {
            "loc": ("field2",),
            "msg": "Field2 must be a string",
            "type": "type_error.str",
        },
    ]

    simplified = simplify_validation_errors(errors)

    assert simplified == {
        "recursive_model - lng": "Field1 is required",
        "field2": "Field2 must be a string",
    }


# Mocking external API responses for the functions involving requests
@pytest.fixture
def mock_requests():
    with (
        mock.patch("requests.post") as mock_post,
        mock.patch("requests.get") as mock_get,
    ):
        yield mock_post, mock_get


# Test validate_xml_file function (mocked)
def test_validate_xml_file(mock_requests):
    mock_post, _ = mock_requests

    # Mock successful API response
    mock_response = mock.Mock()
    mock_response.json.return_value = {"status": "VALID"}
    mock_response.raise_for_status = mock.Mock()
    mock_post.return_value = mock_response

    result = validate_xml_file("<xml>data</xml>", "bro_user", "bro_pass", "12345")
    assert result == {"status": "VALID"}

    # Test request failure
    mock_post.side_effect = requests.exceptions.RequestException("API failure")
    with pytest.raises(RuntimeError, match="Validate xml error: API failure"):
        validate_xml_file("<xml>data</xml>", "bro_user", "bro_pass", "12345")


# Test create_upload_url function (mocked)
def test_create_upload_url(mock_requests):
    mock_post, _ = mock_requests

    # Mock successful API response
    mock_response = mock.Mock()
    mock_response.headers = {
        "Location": "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads"
    }
    mock_response.raise_for_status = mock.Mock()
    mock_post.return_value = mock_response

    result = create_upload_url("bro_user", "bro_pass", "12345")
    assert result == "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads"

    # Test request failure
    mock_post.side_effect = requests.exceptions.RequestException("API failure")
    with pytest.raises(RuntimeError, match="Create upload url error: API failure"):
        create_upload_url("bro_user", "bro_pass", "12345")


# Test add_xml_to_upload function (mocked)
def test_add_xml_to_upload(mock_requests):
    mock_post, _ = mock_requests

    # Mock successful API response
    mock_response = mock.Mock()
    mock_response.headers = {
        "Location": "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads/"
    }
    mock_response.raise_for_status = mock.Mock()
    mock_post.return_value = mock_response

    result = add_xml_to_upload(
        "<xml>data</xml>",
        "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads",
        "bro_user",
        "bro_pass",
    )
    assert result == "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads/"

    # Test request failure
    mock_post.side_effect = requests.exceptions.RequestException("API failure")
    with pytest.raises(RuntimeError, match="Add XML to upload error: API failure"):
        add_xml_to_upload(
            "<xml>data</xml>",
            "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads",
            "bro_user",
            "bro_pass",
        )


# Test create_delivery function (mocked)
def test_create_delivery(mock_requests):
    mock_post, _ = mock_requests

    # Mock successful API response
    mock_response = mock.Mock()
    mock_response.headers = {
        "Location": "https://www.bronhouderportaal-bro.nl/api/v2/1234/leveringen"
    }
    mock_response.raise_for_status = mock.Mock()
    mock_post.return_value = mock_response

    result = create_delivery(
        "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads/0000013524",
        "bro_user",
        "bro_pass",
        "1234",
    )
    assert result == "https://www.bronhouderportaal-bro.nl/api/v2/1234/leveringen"

    # Test request failure
    mock_post.side_effect = requests.exceptions.RequestException("API failure")
    with pytest.raises(RuntimeError, match="Deliver uploaded XML error: API failure"):
        create_delivery(
            "https://www.bronhouderportaal-bro.nl/api/v2/1234/uploads/0000013524",
            "bro_user",
            "bro_pass",
            "1234",
        )


# Test check_delivery_status function (mocked)
def test_check_delivery_status(mock_requests):
    mock_get = mock_requests[1]

    # Mock successful API response
    mock_response = mock.Mock()
    mock_response.json.return_value = {"status": "delivered"}
    mock_get.return_value = mock_response

    result = check_delivery_status(
        "https://www.bronhouderportaal-bro.nl/api/v2/1234/leveringen",
        "bro_user",
        "bro_pass",
    )
    assert result == {"status": "delivered"}

    # Test request failure
    mock_get.side_effect = requests.exceptions.RequestException("API failure")
    with pytest.raises(RuntimeError, match="Delivery info check error: API failure"):
        check_delivery_status(
            "https://www.bronhouderportaal-bro.nl/api/v2/1234/leveringen",
            "bro_user",
            "bro_pass",
        )


# Test include_delivery_responsible_party function
@pytest.mark.django_db
def test_include_delivery_responsible_party():
    import uuid

    _uuid = uuid.uuid4()
    # Simulate an existing Organisation
    Organisation.objects.create(uuid=_uuid, kvk_number="12345678")

    # Test when data_owner is the same as kvk_number
    result = include_delivery_responsible_party("12345678", str(_uuid))
    assert not result  # Responsible party is not included

    # Test when data_owner is different
    result = include_delivery_responsible_party("87654321", str(_uuid))
    assert result  # Responsible party should be included

    # Test when data_owner is None
    result = include_delivery_responsible_party("87654321", None)
    assert result  # Responsible party should be included when no data_owner
