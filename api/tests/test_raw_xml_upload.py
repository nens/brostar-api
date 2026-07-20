"""Tests for the raw XML / ZIP upload endpoint.

Covers:
- parse_raw_xml_metadata() helper
- validate_and_deliver_raw_xml_task() Celery task
- RawXMLUploadView (POST /api/uploadtasks/xml-upload/)

Replace the XML_* constants below with real BRO XML files once available.
Each constant follows the BRO document structure:
  <?xml ...?>
  <{requestType}Request ...>   ← determines request_type
    ...
    <sourceDocument>
      <{RegistrationType} .../>  ← determines registration_type + bro_domain
    </sourceDocument>
  </{requestType}Request>
"""

import io
import zipfile
from unittest import mock

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from api.bro_upload.utils import parse_raw_xml_metadata
from api.models import UploadTask
from api.tasks import validate_and_deliver_raw_xml_task
from api.tests import fixtures

organisation = fixtures.organisation
user = fixtures.user
userprofile = fixtures.userprofile

# ---------------------------------------------------------------------------
# Minimal sample XML strings
# Replace these with real BRO source documents when available.
# ---------------------------------------------------------------------------

XML_GLD_CLOSURE_REGISTRATION = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<registrationRequest xmlns="http://www.broservices.nl/xsd/isgld/1.0"
  xmlns:brocom="http://www.broservices.nl/xsd/brocommon/3.0"
  xmlns:gml="http://www.opengis.net/gml/3.2">
  <brocom:requestReference>test-001</brocom:requestReference>
  <brocom:qualityRegime>IMBRO/A</brocom:qualityRegime>
  <sourceDocument>
    <GLD_Closure gml:id="id_0001" />
  </sourceDocument>
</registrationRequest>
"""

XML_GMW_CONSTRUCTION_REGISTRATION = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<registrationRequest xmlns="http://www.broservices.nl/xsd/isgmw/1.1"
  xmlns:brocom="http://www.broservices.nl/xsd/brocommon/3.0">
  <brocom:requestReference>test-002</brocom:requestReference>
  <brocom:qualityRegime>IMBRO/A</brocom:qualityRegime>
  <sourceDocument>
    <GMW_Construction />
  </sourceDocument>
</registrationRequest>
"""

XML_GMW_GROUND_LEVEL_INSERT = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<insertRequest xmlns="http://www.broservices.nl/xsd/isgmw/1.1"
  xmlns:brocom="http://www.broservices.nl/xsd/brocommon/3.0">
  <brocom:requestReference>test-003</brocom:requestReference>
  <brocom:qualityRegime>IMBRO/A</brocom:qualityRegime>
  <sourceDocument>
    <GMW_GroundLevel />
  </sourceDocument>
</insertRequest>
"""

XML_GMW_CONSTRUCTION_REPLACE = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<replaceRequest xmlns="http://www.broservices.nl/xsd/isgmw/1.1"
  xmlns:brocom="http://www.broservices.nl/xsd/brocommon/3.0">
  <brocom:requestReference>test-004</brocom:requestReference>
  <brocom:qualityRegime>IMBRO/A</brocom:qualityRegime>
  <sourceDocument>
    <GMW_Construction />
  </sourceDocument>
</replaceRequest>
"""

XML_GMW_REMOVAL_DELETE = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<deleteRequest xmlns="http://www.broservices.nl/xsd/isgmw/1.1"
  xmlns:brocom="http://www.broservices.nl/xsd/brocommon/3.0">
  <brocom:requestReference>test-005</brocom:requestReference>
  <brocom:qualityRegime>IMBRO/A</brocom:qualityRegime>
  <sourceDocument>
    <GMW_Removal />
  </sourceDocument>
</deleteRequest>
"""

XML_GMW_GROUND_LEVEL_MOVE = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<moveRequest xmlns="http://www.broservices.nl/xsd/isgmw/1.1"
  xmlns:brocom="http://www.broservices.nl/xsd/brocommon/3.0">
  <brocom:requestReference>test-006</brocom:requestReference>
  <brocom:qualityRegime>IMBRO/A</brocom:qualityRegime>
  <sourceDocument>
    <GMW_GroundLevel />
  </sourceDocument>
</moveRequest>
"""

XML_MALFORMED = b"this is not xml at all"

XML_NO_SOURCE_DOCUMENT = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<registrationRequest xmlns="http://www.broservices.nl/xsd/isgld/1.0"
  xmlns:brocom="http://www.broservices.nl/xsd/brocommon/3.0">
  <brocom:requestReference>test-bad</brocom:requestReference>
</registrationRequest>
"""

XML_EMPTY_SOURCE_DOCUMENT = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<registrationRequest xmlns="http://www.broservices.nl/xsd/isgld/1.0">
  <sourceDocument />
</registrationRequest>
"""

XML_UNKNOWN_ROOT = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<unknownRequest xmlns="http://www.broservices.nl/xsd/isgld/1.0">
  <sourceDocument>
    <GLD_Closure />
  </sourceDocument>
</unknownRequest>
"""

URL = "/api/uploadtasks/xml-upload/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_zip(*entries: tuple[str, bytes]) -> bytes:
    """Build an in-memory ZIP from (filename, content) pairs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in entries:
            zf.writestr(name, data)
    return buf.getvalue()


# ===========================================================================
# parse_raw_xml_metadata
# ===========================================================================


class TestParseRawXmlMetadata:
    def test_registration_gld_closure(self):
        meta = parse_raw_xml_metadata(XML_GLD_CLOSURE_REGISTRATION)
        assert meta["request_type"] == "registration"
        assert meta["registration_type"] == "GLD_Closure"
        assert meta["bro_domain"] == "GLD"

    def test_registration_gmw_construction(self):
        meta = parse_raw_xml_metadata(XML_GMW_CONSTRUCTION_REGISTRATION)
        assert meta["request_type"] == "registration"
        assert meta["registration_type"] == "GMW_Construction"
        assert meta["bro_domain"] == "GMW"

    def test_insert_request(self):
        meta = parse_raw_xml_metadata(XML_GMW_GROUND_LEVEL_INSERT)
        assert meta["request_type"] == "insert"
        assert meta["registration_type"] == "GMW_GroundLevel"
        assert meta["bro_domain"] == "GMW"

    def test_replace_request(self):
        meta = parse_raw_xml_metadata(XML_GMW_CONSTRUCTION_REPLACE)
        assert meta["request_type"] == "replace"

    def test_delete_request(self):
        meta = parse_raw_xml_metadata(XML_GMW_REMOVAL_DELETE)
        assert meta["request_type"] == "delete"
        assert meta["registration_type"] == "GMW_Removal"

    def test_move_request(self):
        meta = parse_raw_xml_metadata(XML_GMW_GROUND_LEVEL_MOVE)
        assert meta["request_type"] == "move"

    def test_malformed_xml_raises(self):
        with pytest.raises(ValueError, match="XML parse error"):
            parse_raw_xml_metadata(XML_MALFORMED)

    def test_no_source_document_raises(self):
        with pytest.raises(ValueError, match="sourceDocument"):
            parse_raw_xml_metadata(XML_NO_SOURCE_DOCUMENT)

    def test_empty_source_document_raises(self):
        with pytest.raises(ValueError):
            parse_raw_xml_metadata(XML_EMPTY_SOURCE_DOCUMENT)

    def test_unknown_root_raises(self):
        with pytest.raises(ValueError, match="Unrecognised root element"):
            parse_raw_xml_metadata(XML_UNKNOWN_ROOT)


# ===========================================================================
# validate_and_deliver_raw_xml_task
# ===========================================================================


class TestValidateAndDeliverRawXmlTask:
    """Tests use mocks only — no database required."""

    def _make_task_mock(self):
        task = mock.Mock()
        task.project_number = "1234"
        task.status = "PENDING"
        return task

    @mock.patch("api.tasks.utils.validate_xml_file")
    @mock.patch("api.tasks.api_models.UploadTask.objects.get")
    def test_cache_miss_marks_task_failed(self, mock_get, mock_validate):
        mock_get.return_value = self._make_task_mock()
        with (
            mock.patch("django.core.cache.cache.get", return_value=None),
        ):
            validate_and_deliver_raw_xml_task("uuid", "user", "pass", "key")

        task = mock_get.return_value
        assert task.status == "FAILED"
        assert "verlopen" in task.log
        mock_validate.assert_not_called()

    @mock.patch("api.tasks.utils.validate_xml_file")
    @mock.patch("api.tasks.api_models.UploadTask.objects.get")
    def test_validation_failure_marks_task_failed(self, mock_get, mock_validate):
        mock_get.return_value = self._make_task_mock()
        mock_validate.return_value = {
            "status": "NIET-VALIDE",
            "errors": ["Veld X ontbreekt"],
        }
        xml_str = XML_GLD_CLOSURE_REGISTRATION.decode()

        with (
            mock.patch("django.core.cache.cache.get", return_value=xml_str),
            mock.patch("django.core.cache.cache.delete") as mock_delete,
        ):
            validate_and_deliver_raw_xml_task("uuid", "user", "pass", "key")

        task = mock_get.return_value
        assert task.status == "FAILED"
        assert "Veld X ontbreekt" in task.bro_errors
        mock_delete.assert_called_once_with("key")

    @mock.patch("api.tasks.check_delivery_status_task")
    @mock.patch("api.tasks.utils.create_delivery")
    @mock.patch("api.tasks.utils.add_xml_to_upload")
    @mock.patch("api.tasks.utils.create_upload_url")
    @mock.patch("api.tasks.utils.validate_xml_file")
    @mock.patch("api.tasks.api_models.UploadTask.objects.get")
    def test_valid_xml_triggers_delivery_chain(
        self,
        mock_get,
        mock_validate,
        mock_create_upload,
        mock_add_xml,
        mock_create_delivery,
        mock_check_status,
    ):
        mock_get.return_value = self._make_task_mock()
        mock_validate.return_value = {"status": "VALIDE", "errors": []}
        mock_create_upload.return_value = {
            "status": "OK",
            "upload_url": "http://bro/api/v2/1234/uploads/99",
        }
        mock_add_xml.return_value = "http://bro/api/v2/1234/uploads/99/brondocumenten/1"
        mock_create_delivery.return_value = "http://bro/api/v2/1234/leveringen/42"
        xml_str = XML_GLD_CLOSURE_REGISTRATION.decode()

        with (
            mock.patch("django.core.cache.cache.get", return_value=xml_str),
            mock.patch("django.core.cache.cache.delete") as mock_delete,
        ):
            validate_and_deliver_raw_xml_task("uuid", "user", "pass", "key")

        task = mock_get.return_value
        assert task.bro_delivery_url == "http://bro/api/v2/1234/leveringen/42"
        mock_delete.assert_called_once_with("key")

    @mock.patch("api.tasks.utils.validate_xml_file", side_effect=Exception("boom"))
    @mock.patch("api.tasks.api_models.UploadTask.objects.get")
    def test_unexpected_exception_marks_task_failed(self, mock_get, mock_validate):
        mock_get.return_value = self._make_task_mock()
        xml_str = XML_GLD_CLOSURE_REGISTRATION.decode()

        with (
            mock.patch("django.core.cache.cache.get", return_value=xml_str),
            mock.patch("django.core.cache.cache.delete") as mock_delete,
        ):
            validate_and_deliver_raw_xml_task("uuid", "user", "pass", "key")

        task = mock_get.return_value
        assert task.status == "FAILED"
        mock_delete.assert_called_once_with("key")


# ===========================================================================
# RawXMLUploadView
# ===========================================================================


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user, userprofile):  # noqa: F811
    """Authenticated client with a user that has an org and BRO credentials."""
    api_client.force_authenticate(user=user)
    return api_client


def _xml_upload(
    client,
    content: bytes,
    filename: str = "upload.xml",
    project_number: str = "9999",
    content_type: str = "text/xml",
):
    from django.core.files.uploadedfile import SimpleUploadedFile

    f = SimpleUploadedFile(filename, content, content_type=content_type)
    return client.post(
        URL,
        {"file": f, "project_number": project_number},
        format="multipart",
    )


def _zip_upload(client, *entries: tuple[str, bytes], project_number: str = "9999"):
    from django.core.files.uploadedfile import SimpleUploadedFile

    zip_bytes = _make_zip(*entries)
    f = SimpleUploadedFile("upload.zip", zip_bytes, content_type="application/zip")
    return client.post(
        URL,
        {"file": f, "project_number": project_number},
        format="multipart",
    )


# --- authentication / authorisation ----------------------------------------


def test_unauthenticated_request_returns_401(api_client):
    from django.core.files.uploadedfile import SimpleUploadedFile

    f = SimpleUploadedFile("x.xml", XML_GLD_CLOSURE_REGISTRATION)
    response = api_client.post(
        URL, {"file": f, "project_number": "1"}, format="multipart"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_no_organisation_returns_400(api_client, user):
    """User exists but has no organisation linked."""
    api_client.force_authenticate(user=user)
    response = _xml_upload(api_client, XML_GLD_CLOSURE_REGISTRATION)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "organisation" in response.data["detail"].lower()


@pytest.mark.django_db
def test_no_bro_credentials_returns_400(api_client, user, userprofile):
    """Organisation linked but BRO credentials are blank."""
    userprofile.organisation.bro_user_token = ""
    userprofile.organisation.bro_user_password = ""
    userprofile.organisation.save()

    api_client.force_authenticate(user=user)
    response = _xml_upload(api_client, XML_GLD_CLOSURE_REGISTRATION)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "credentials" in response.data["detail"].lower()


# --- request validation -----------------------------------------------------


@pytest.mark.django_db
def test_missing_project_number_returns_400(auth_client):
    from django.core.files.uploadedfile import SimpleUploadedFile

    f = SimpleUploadedFile("x.xml", XML_GLD_CLOSURE_REGISTRATION)
    response = auth_client.post(URL, {"file": f}, format="multipart")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "project_number" in response.data["detail"].lower()


@pytest.mark.django_db
def test_missing_file_returns_400(auth_client):
    response = auth_client.post(URL, {"project_number": "9999"}, format="multipart")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "bestand" in response.data["detail"].lower()


@pytest.mark.django_db
def test_non_xml_non_zip_content_returns_400(auth_client):
    response = _xml_upload(auth_client, b"not xml or zip content here!", "file.xml")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_malformed_xml_single_file_returns_400(auth_client):
    """A single file that isn't valid XML (but starts with <) is processed and
    parse_raw_xml_metadata raises ValueError → 400 because no valid entries remain."""
    response = _xml_upload(auth_client, b"<not-a-bro-document/>", "bad.xml")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# --- single XML upload ------------------------------------------------------


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_single_valid_xml_returns_202(mock_cache, mock_task, auth_client):
    mock_task.delay = mock.Mock()

    response = _xml_upload(auth_client, XML_GLD_CLOSURE_REGISTRATION, "gld_closure.xml")

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.data
    assert len(data["created"]) == 1
    created = data["created"][0]
    assert created["filename"] == "gld_closure.xml"
    assert created["registration_type"] == "GLD_Closure"
    assert created["request_type"] == "registration"
    assert "uuid" in created


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_single_valid_xml_creates_upload_task(mock_cache, mock_task, auth_client):
    mock_task.delay = mock.Mock()

    _xml_upload(auth_client, XML_GLD_CLOSURE_REGISTRATION, "gld_closure.xml")

    task = UploadTask.objects.first()
    assert task is not None
    assert task.registration_type == "GLD_Closure"
    assert task.request_type == "registration"
    assert task.bro_domain == "GLD"
    assert task.status == "PENDING"
    assert task.sourcedocument_data["filename"] == "gld_closure.xml"
    assert task.metadata["_is_raw_xml"] is True


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_single_valid_xml_fires_celery_task(mock_cache, mock_task, auth_client):
    mock_task.delay = mock.Mock()

    _xml_upload(auth_client, XML_GLD_CLOSURE_REGISTRATION)

    mock_task.delay.assert_called_once()
    call_args = mock_task.delay.call_args[0]
    # args: (upload_task_uuid, bro_username, bro_password, cache_key)
    assert call_args[1] == "secret"  # bro_user_token from fixtures.organisation
    assert call_args[2] == "secret"  # bro_user_password from fixtures.organisation
    assert call_args[3].startswith("raw_xml_")


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_single_valid_xml_stores_bytes_in_cache(mock_cache, mock_task, auth_client):
    mock_task.delay = mock.Mock()

    _xml_upload(auth_client, XML_GLD_CLOSURE_REGISTRATION)

    mock_cache.set.assert_called_once()
    # cache.set(key, value, timeout=...) — timeout is a kwarg, only 2 positional args
    call_args = mock_cache.set.call_args
    _key, xml_string = call_args[0]
    assert "GLD_Closure" in xml_string


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_insert_request_type_detected(mock_cache, mock_task, auth_client):
    mock_task.delay = mock.Mock()

    response = _xml_upload(auth_client, XML_GMW_GROUND_LEVEL_INSERT, "gmw_insert.xml")

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.data["created"][0]["request_type"] == "insert"


# --- ZIP upload -------------------------------------------------------------


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_zip_with_two_xmls_returns_202_and_two_tasks(
    mock_cache, mock_task, auth_client
):
    mock_task.delay = mock.Mock()

    response = _zip_upload(
        auth_client,
        ("gld.xml", XML_GLD_CLOSURE_REGISTRATION),
        ("gmw.xml", XML_GMW_CONSTRUCTION_REGISTRATION),
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert len(response.data["created"]) == 2
    assert UploadTask.objects.count() == 2
    assert mock_task.delay.call_count == 2


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_zip_skips_non_xml_entries(mock_cache, mock_task, auth_client):
    mock_task.delay = mock.Mock()

    response = _zip_upload(
        auth_client,
        ("valid.xml", XML_GLD_CLOSURE_REGISTRATION),
        ("readme.txt", b"ignore me"),
        ("image.png", b"\x89PNG\r\n\x1a\n"),
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert len(response.data["created"]) == 1
    assert "skipped" not in response.data  # non-XML entries silently ignored


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_zip_skips_malformed_xml_entry(mock_cache, mock_task, auth_client):
    """Malformed XML inside a ZIP is skipped; valid entries still succeed."""
    mock_task.delay = mock.Mock()

    response = _zip_upload(
        auth_client,
        ("valid.xml", XML_GLD_CLOSURE_REGISTRATION),
        ("bad.xml", XML_MALFORMED),
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert len(response.data["created"]) == 1
    assert "bad.xml" in response.data.get("skipped", [])


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_zip_with_only_malformed_entries_returns_400(
    mock_cache, mock_task, auth_client
):
    mock_task.delay = mock.Mock()

    response = _zip_upload(auth_client, ("bad.xml", XML_MALFORMED))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_zip_path_traversal_entry_is_sanitised(mock_cache, mock_task, auth_client):
    """A ZIP entry with a path-traversal name is silently skipped."""
    mock_task.delay = mock.Mock()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        # Manually write an entry with a dangerous name
        info = zipfile.ZipInfo("../../etc/passwd.xml")
        zf.writestr(info, XML_GLD_CLOSURE_REGISTRATION)
    zip_bytes = buf.getvalue()

    from django.core.files.uploadedfile import SimpleUploadedFile

    f = SimpleUploadedFile("evil.zip", zip_bytes, content_type="application/zip")
    response = auth_client.post(
        URL, {"file": f, "project_number": "9999"}, format="multipart"
    )

    # Entry is skipped → no valid XMLs → 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_zip_exceeding_size_limit_returns_400(auth_client, settings):
    """ZIP file that exceeds RAW_XML_MAX_ZIP_MB is rejected before processing."""
    settings.RAW_XML_MAX_ZIP_MB = 0  # Force limit to 0 MB

    response = _zip_upload(auth_client, ("x.xml", XML_GLD_CLOSURE_REGISTRATION))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "MB" in response.data["detail"]


@pytest.mark.django_db
def test_single_xml_exceeding_size_limit_returns_400(auth_client, settings):
    settings.RAW_XML_MAX_XML_MB = 0  # Force limit to 0 MB

    response = _xml_upload(auth_client, XML_GLD_CLOSURE_REGISTRATION)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "MB" in response.data["detail"]


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_zip_entry_count_capped_at_max(mock_cache, mock_task, auth_client, settings):
    """ZIP entries beyond RAW_XML_MAX_ZIP_ENTRIES are silently dropped."""
    settings.RAW_XML_MAX_ZIP_ENTRIES = 2
    mock_task.delay = mock.Mock()

    entries = [(f"file_{i}.xml", XML_GLD_CLOSURE_REGISTRATION) for i in range(5)]
    response = _zip_upload(auth_client, *entries)

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert len(response.data["created"]) == 2


# --- response shape ---------------------------------------------------------


@pytest.mark.django_db
@mock.patch("api.views.tasks.validate_and_deliver_raw_xml_task")
@mock.patch("api.views.cache")
def test_response_contains_expected_keys(mock_cache, mock_task, auth_client):
    mock_task.delay = mock.Mock()

    response = _xml_upload(auth_client, XML_GLD_CLOSURE_REGISTRATION, "gld.xml")

    assert response.status_code == status.HTTP_202_ACCEPTED
    created = response.data["created"][0]
    assert set(created.keys()) == {
        "uuid",
        "filename",
        "registration_type",
        "request_type",
    }
