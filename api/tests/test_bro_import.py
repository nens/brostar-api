import pytest
from django.conf import settings
from requests.exceptions import RequestException

from api.bro_import import bulk_import
from api.tests import fixtures

organisation = fixtures.organisation
importtask = fixtures.importtask


@pytest.fixture
def bulk_importer(importtask):
    return bulk_import.BulkImporter(importtask.uuid)


@pytest.mark.django_db
def test_create_bro_ids_import_url(bulk_importer):
    url = bulk_importer._create_bro_ids_import_url()
    assert (
        url
        == f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/gmn/v1/bro-ids?bronhouder=12345678"
    )


@pytest.mark.django_db
def test_fetch_bro_ids_succes(mocker, bulk_importer):
    expected_bro_ids = ["BRO123", "BRO456", "BRO789"]
    mock_response = mocker.Mock()
    mock_response.json.return_value = {"broIds": expected_bro_ids}
    mock_response.raise_for_status = mocker.Mock()
    mocker.patch("requests.get", return_value=mock_response)

    bro_ids = bulk_importer._fetch_bro_ids(
        f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/gmn/v1/bro-ids?bronhouder=12345678"
    )

    assert expected_bro_ids == bro_ids


@pytest.mark.django_db
def test_fetch_bro_ids_fail(mocker, bulk_importer):
    mocker.patch("requests.get", side_effect=RequestException("An error occurred"))

    with pytest.raises(bulk_import.FetchBROIDsError):
        bulk_importer._fetch_bro_ids("url.com")
