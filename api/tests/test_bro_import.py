import pytest
from django.conf import settings
from requests.exceptions import HTTPError, RequestException

from api.bro_import import bulk_import, object_import
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


@pytest.fixture
def gmn_object_importer(organisation):
    return object_import.GMNObjectImporter(
        bro_id="GMN1234567890", data_owner=organisation.uuid
    )


@pytest.mark.django_db
def test_object_importer_create_download_url(gmn_object_importer):
    url = gmn_object_importer._create_download_url()

    assert (
        url
        == f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/gmn/v1/objects/GMN1234567890?fullHistory=nee"
    )


@pytest.mark.django_db
def test_object_importer_download_xml(mocker, gmn_object_importer):
    expected_content = b"<xml>fake_data</xml>"
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.raise_for_status = mocker.Mock()
    mock_response.content = expected_content
    mock_get.return_value = mock_response

    # Test
    url = "https://example.com/data.xml"
    result = gmn_object_importer._download_xml(url)

    # Assert
    assert result == expected_content


@pytest.mark.django_db
def test_download_xml_http_error(mocker, gmn_object_importer):
    # Setup
    mock_get = mocker.patch("requests.get")
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = HTTPError("Error occurred")
    mock_get.return_value = mock_response

    # Test
    url = "https://example.com/data.xml"

    # Assert that an HTTPError is raised
    with pytest.raises(HTTPError):
        gmn_object_importer._download_xml(url)


@pytest.mark.django_db
def test_convert_xml_to_json(gmn_object_importer):
    xml = b"<xml>fake_data</xml>"
    expected_json = {"xml": "fake_data"}

    json_data = gmn_object_importer._convert_xml_to_json(xml)

    assert json_data == expected_json


@pytest.fixture
def gld_object_importer(organisation):
    return object_import.GLDObjectImporter(
        bro_id="GLD000000076615", data_owner=organisation
    )


@pytest.mark.django_db
def test_gld_download_url(gld_object_importer: object_import.GLDObjectImporter):
    url = gld_object_importer._create_download_url()

    assert (
        url
        == f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/gld/v1/objects/GLD000000076615?fullHistory=nee&observationPeriodBeginDate=2021-01-01&observationPeriodEndDate=2021-01-01"
    )


@pytest.mark.django_db
def test_gld_observation_summary(gld_object_importer: object_import.GLDObjectImporter):
    observation_summary = gld_object_importer._observation_summary()

    assert isinstance(observation_summary, list)

    procedure = observation_summary[0]
    assert isinstance(procedure, dict)

    keys = procedure.keys()
    assert "observationId" in keys
    assert "startDate" in keys
    assert "endDate" in keys
    assert "observationType" in keys
    assert "observationProcessId" in keys


@pytest.mark.django_db
def test_gld_import(gld_object_importer: object_import.GLDObjectImporter):
    gld_object_importer.run()
