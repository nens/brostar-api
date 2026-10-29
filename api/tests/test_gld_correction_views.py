"""End-to-end tests for the GLD correction endpoints."""

import json
from pathlib import Path
from unittest import mock

import pytest
from django.urls import Resolver404, resolve, reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.bro_upload.object_upload import XMLGenerator
from api.corrections.exceptions import BROUnavailable, ObservationNotFound
from api.models import UploadTask
from api.tests import fixtures

organisation = fixtures.organisation
user = fixtures.user
userprofile = fixtures.userprofile

XML_DIR = Path(__file__).parent / "xml_strings"
GLD_XML = (XML_DIR / "gld_correction_GLD000000000024.xml").read_text(encoding="utf-8")
GLD_SUMMARIES = json.loads(
    (XML_DIR / "gld_correction_GLD000000000024_summaries.json").read_text(
        encoding="utf-8"
    )
)

GLD_ID = "GLD000000000024"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def bro(monkeypatch):
    """Mock the public BRO restservice; it is never contacted for real."""
    from api.corrections.gld import client

    fetch_xml = mock.Mock(return_value=GLD_XML)
    fetch_summaries = mock.Mock(return_value=GLD_SUMMARIES)
    monkeypatch.setattr(client, "fetch_observation_xml", fetch_xml)
    monkeypatch.setattr(client, "fetch_observation_summaries", fetch_summaries)

    return mock.Mock(xml=fetch_xml, summaries=fetch_summaries)


@pytest.fixture
def celery(monkeypatch):
    """Keep the post_save signal from starting an actual delivery."""
    from api import signals

    upload = mock.Mock()
    monkeypatch.setattr(signals.tasks, "upload_task", upload)
    return upload


def login(api_client, user):
    """Authenticate, with a user whose cached profile is up to date."""
    user.refresh_from_db()
    api_client.force_authenticate(user=user)


def measurements_url(observation_id: str = "observationId_001") -> str:
    return reverse(
        "api:gld-correction-measurements",
        kwargs={"gld_id": GLD_ID, "observation_id": observation_id},
    )


def procedure_url(observation_id: str = "observationId_001") -> str:
    return reverse(
        "api:gld-correction-procedure",
        kwargs={"gld_id": GLD_ID, "observation_id": observation_id},
    )


def post(api_client, url, payload, **params):
    if params:
        query = "&".join(f"{key}={value}" for key, value in params.items())
        url = f"{url}?{query}"
    return api_client.post(url, payload, format="json")


# --------------------------------------------------------------------- routing


def test_correction_urls():
    base = f"/api/uploadtask/correction/gld/{GLD_ID}/addition/observationId_001"

    assert measurements_url() == f"{base}/measurements/"
    assert procedure_url() == f"{base}/procedure/"


def test_legacy_correction_urls_no_longer_resolve():
    with pytest.raises(Resolver404):
        resolve(
            f"/api/uploadtask/correction/gld/{GLD_ID}/observationId_001/measurements/"
        )


# ------------------------------------------------------------------ happy flow


@pytest.mark.django_db
def test_exact_match_replaces_measurement(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)

    response = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "measurements": [
                {"time": "2021-01-05T12:00:00+01:00", "value": 0.99},
            ],
        },
    )

    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["measurements_changed"] == 1

    task = UploadTask.objects.get(uuid=response.data["uuid"])
    assert task.registration_type == "GLD_Addition"
    assert task.request_type == "replace"
    assert task.bro_domain == "GLD"
    assert task.project_number == "1255"
    assert task.data_owner == organisation
    assert task.metadata["correctionReason"] == "eigenCorrectie"
    assert task.metadata["broId"] == GLD_ID

    tvps = task.sourcedocument_data["timeValuePairs"]
    assert len(tvps) == 5
    assert tvps[1] == {
        "time": "2021-01-05T12:00:00+01:00",
        "value": 0.99,
        "statusQualityControl": "onbekend",
        "censorReason": None,
        "censoringLimitvalue": None,
    }
    # Untouched measurements keep their original values.
    assert tvps[0]["value"] == 0.52
    assert tvps[3]["value"] == 0.61
    assert tvps[4]["censorReason"] == "kleinerDanLimietwaarde"

    # The observation period did not change.
    assert task.sourcedocument_data["beginPosition"] == "2021-01-04"
    assert task.sourcedocument_data["endPosition"] == "2021-01-08"
    celery.assert_called_once()


@pytest.mark.django_db
def test_new_measurement_within_period_is_added(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)

    response = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "measurements": [
                {"time": "2021-01-06T06:00:00+01:00", "value": 0.57},
            ],
        },
    )

    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["measurements_changed"] == 1

    task = UploadTask.objects.get(uuid=response.data["uuid"])
    times = [tvp["time"] for tvp in task.sourcedocument_data["timeValuePairs"]]
    assert times == [
        "2021-01-04T12:00:00+01:00",
        "2021-01-05T12:00:00+01:00",
        "2021-01-06T06:00:00+01:00",
        "2021-01-06T12:00:00+01:00",
        "2021-01-07T12:00:00+01:00",
        "2021-01-08T12:00:00+01:00",
    ]
    assert task.sourcedocument_data["beginPosition"] == "2021-01-04"
    assert task.sourcedocument_data["endPosition"] == "2021-01-08"

    # Rule 5 does not apply, so the observation summary is not requested.
    bro.summaries.assert_not_called()


@pytest.mark.django_db
def test_measurement_outside_period_extends_observation(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)

    response = post(
        api_client,
        measurements_url("observationId_002"),
        {
            "project_number": "1255",
            "measurements": [
                {"time": "2021-04-10T12:00:00+02:00", "value": 1.21},
            ],
        },
    )

    assert response.status_code == status.HTTP_201_CREATED, response.data
    bro.summaries.assert_called_once_with(GLD_ID)

    task = UploadTask.objects.get(uuid=response.data["uuid"])
    assert task.sourcedocument_data["beginPosition"] == "2021-03-29"
    assert task.sourcedocument_data["endPosition"] == "2021-04-10"
    assert task.sourcedocument_data["resultTime"] == "2021-04-10T12:00:00+02:00"
    assert len(task.sourcedocument_data["timeValuePairs"]) == 4


@pytest.mark.django_db
def test_measurement_outside_period_with_better_observation(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)

    response = post(
        api_client,
        measurements_url("observationId_001"),
        {
            "project_number": "1255",
            "measurements": [
                {"time": "2021-03-28T12:00:00+02:00", "value": 1.11},
            ],
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "observationId_002" in str(response.data)
    assert UploadTask.objects.count() == 0


@pytest.mark.django_db
def test_delta_t_overwrites_shifted_measurement(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)

    response = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "measurements": [
                {"time": "2021-01-05T12:02:00+01:00", "value": 0.56},
            ],
        },
        delta_t=300,
    )

    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["measurements_changed"] == 1

    task = UploadTask.objects.get(uuid=response.data["uuid"])
    times = [tvp["time"] for tvp in task.sourcedocument_data["timeValuePairs"]]
    assert "2021-01-05T12:02:00+01:00" in times
    assert "2021-01-05T12:00:00+01:00" not in times
    assert len(times) == 5


@pytest.mark.django_db
def test_delta_t_with_multiple_matches(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)

    response = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "measurements": [
                {"time": "2021-01-05T18:00:00+01:00", "value": 0.56},
            ],
        },
        delta_t=172800,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "delta_t" in str(response.data)
    assert UploadTask.objects.count() == 0


@pytest.mark.django_db
def test_procedure_correction(api_client, user, userprofile, organisation, bro, celery):
    login(api_client, user)

    response = post(
        api_client,
        procedure_url(),
        {
            "project_number": "6708",
            "correction_reason": "kwaliteitsregime",
            "procedure": {
                "evaluationProcedure": "oordeelDeskundige",
                "measurementInstrumentType": "druksensor",
            },
        },
    )

    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["variables_changed"] == 2

    task = UploadTask.objects.get(uuid=response.data["uuid"])
    assert task.metadata["correctionReason"] == "kwaliteitsregime"
    assert task.sourcedocument_data["evaluationProcedure"] == "oordeelDeskundige"
    assert task.sourcedocument_data["measurementInstrumentType"] == "druksensor"
    assert task.sourcedocument_data["processReference"] == "NEN5120v1991"
    assert len(task.sourcedocument_data["timeValuePairs"]) == 5


@pytest.mark.django_db
def test_procedure_correction_of_referenced_procedure(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)

    response = post(
        api_client,
        procedure_url("observationId_003"),
        {
            "project_number": "6708",
            "procedure": {"evaluationProcedure": "oordeelDeskundige"},
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "ObservationProcessId_002" in str(response.data)


# ------------------------------------------------------------------ validation


@pytest.mark.django_db
def test_wrong_body_fields_are_rejected(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)

    procedure_response = post(
        api_client,
        procedure_url(),
        {
            "project_number": "1255",
            "procedure": {"evaluationProcedure": "oordeelDeskundige"},
            "measurements": [{"time": "2021-01-05T12:00:00+01:00", "value": 0.1}],
        },
    )
    measurement_response = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "measurements": [{"time": "2021-01-05T12:00:00+01:00", "value": 0.1}],
            "procedure": {"evaluationProcedure": "oordeelDeskundige"},
        },
    )

    assert procedure_response.status_code == status.HTTP_400_BAD_REQUEST
    assert measurement_response.status_code == status.HTTP_400_BAD_REQUEST
    assert UploadTask.objects.count() == 0


@pytest.mark.django_db
def test_unknown_observation_id(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)

    response = post(
        api_client,
        measurements_url("observationId_999"),
        {
            "project_number": "1255",
            "measurements": [{"time": "2021-01-05T12:00:00+01:00", "value": 0.1}],
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "observationId_999" in str(response.data)


@pytest.mark.django_db
def test_observation_unknown_at_the_bro(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)
    bro.xml.side_effect = ObservationNotFound(GLD_ID, "observationId_404")

    response = post(
        api_client,
        measurements_url("observationId_404"),
        {
            "project_number": "1255",
            "measurements": [{"time": "2021-01-05T12:00:00+01:00", "value": 0.1}],
        },
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_invalid_project_number_and_correction_reason(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)
    measurements = [{"time": "2021-01-05T12:00:00+01:00", "value": 0.1}]

    missing = post(api_client, measurements_url(), {"measurements": measurements})
    not_a_number = post(
        api_client,
        measurements_url(),
        {"project_number": "project-1255", "measurements": measurements},
    )
    wrong_reason = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "correction_reason": "zomaar",
            "measurements": measurements,
        },
    )

    assert missing.status_code == status.HTTP_400_BAD_REQUEST
    assert not_a_number.status_code == status.HTTP_400_BAD_REQUEST
    assert wrong_reason.status_code == status.HTTP_400_BAD_REQUEST
    assert UploadTask.objects.count() == 0


@pytest.mark.django_db
def test_not_logged_in(api_client, bro, celery):
    response = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "measurements": [{"time": "2021-01-05T12:00:00+01:00", "value": 0.1}],
        },
    )

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.django_db
def test_user_without_organisation(api_client, user, bro, celery):
    login(api_client, user)

    response = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "measurements": [{"time": "2021-01-05T12:00:00+01:00", "value": 0.1}],
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert UploadTask.objects.count() == 0


@pytest.mark.django_db
def test_bro_unavailable(api_client, user, userprofile, organisation, bro, celery):
    login(api_client, user)
    bro.xml.side_effect = BROUnavailable()

    response = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "measurements": [{"time": "2021-01-05T12:00:00+01:00", "value": 0.1}],
        },
    )

    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert UploadTask.objects.count() == 0


# ------------------------------------------------------------------------ kvk


@pytest.mark.django_db
def test_kvk_sources(api_client, user, userprofile, organisation, bro, celery):
    login(api_client, user)
    measurements = [{"time": "2021-01-05T12:00:00+01:00", "value": 0.99}]

    default = post(
        api_client,
        measurements_url(),
        {"project_number": "1255", "measurements": measurements},
    )
    explicit = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "investigator_kvk": "99999999",
            "measurements": measurements,
        },
    )
    from_organisation = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "use_organisation_kvk": True,
            "measurements": measurements,
        },
    )

    default_task = UploadTask.objects.get(uuid=default.data["uuid"])
    explicit_task = UploadTask.objects.get(uuid=explicit.data["uuid"])
    organisation_task = UploadTask.objects.get(uuid=from_organisation.data["uuid"])

    assert default_task.sourcedocument_data["investigatorKvk"] == "20164929"
    assert explicit_task.sourcedocument_data["investigatorKvk"] == "99999999"
    assert organisation_task.sourcedocument_data["investigatorKvk"] == "12345678"


@pytest.mark.django_db
def test_organisation_kvk_without_kvk_number(
    api_client, user, userprofile, organisation, bro, celery
):
    organisation.kvk_number = ""
    organisation.save()
    login(api_client, user)

    response = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "use_organisation_kvk": True,
            "measurements": [{"time": "2021-01-05T12:00:00+01:00", "value": 0.1}],
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# -------------------------------------------------------------------- template


@pytest.mark.django_db
def test_sourcedocument_renders_to_xml(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)

    response = post(
        api_client,
        measurements_url(),
        {
            "project_number": "1255",
            "measurements": [{"time": "2021-01-05T12:00:00+01:00", "value": 0.99}],
        },
    )
    task = UploadTask.objects.get(uuid=response.data["uuid"])

    generator = XMLGenerator(
        registration_type="GLD_Addition",
        request_type="replace",
        metadata=task.metadata,
        sourcedocs_data=task.sourcedocument_data,
    )
    xml = generator.create_xml_file()

    assert "<correctionReason" in xml
    assert "eigenCorrectie" in xml
    assert 'gml:id="observationId_001"' in xml
    assert 'gml:id="ObservationProcessId_001"' in xml
    assert '<wml2:value uom="m">0.99</wml2:value>' in xml
    assert xml.count("<wml2:MeasurementTVP>") == 5
