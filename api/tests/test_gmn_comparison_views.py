from datetime import UTC, datetime
from pathlib import Path
from unittest import mock

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.bro_upload.object_upload import XMLGenerator
from api.corrections.exceptions import BROUnavailable, ObjectNotFound
from api.models import UploadTask
from api.tests import fixtures

organisation = fixtures.organisation
user = fixtures.user
userprofile = fixtures.userprofile

# A: GMW...001 tube 1, B: GMW...003 tube 2, C and D ended.
GMN_XML = (
    Path(__file__).parent / "xml_strings" / "gmn_comparison_ended_point.xml"
).read_text(encoding="utf-8")
GMN_ID = "GMN000000000999"

A = {"measuring_point_code": "A", "bro_id": "GMW000000000001", "tube_number": 1}
B = {"measuring_point_code": "B", "bro_id": "GMW000000000003", "tube_number": 2}
NEW_E = {"measuring_point_code": "E", "bro_id": "GMW000000000006", "tube_number": 1}


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def bro(monkeypatch):
    """Mock the public BRO; it is never contacted for real."""
    from api.comparisons.gmn import client

    fetch = mock.Mock(return_value=GMN_XML)
    monkeypatch.setattr(client, "fetch_gmn_xml", fetch)
    return fetch


@pytest.fixture
def celery(monkeypatch):
    """Keep the post_save signal from starting an actual delivery."""
    from api import signals

    upload = mock.Mock()
    monkeypatch.setattr(signals.tasks, "upload_task", upload)
    return upload


def login(api_client, user):
    user.refresh_from_db()
    api_client.force_authenticate(user=user)


def url(gmn_id: str = GMN_ID) -> str:
    return reverse("api:gmn-comparison", kwargs={"gmn_id": gmn_id})


def post(api_client, payload, gmn_id: str = GMN_ID):
    return api_client.post(url(gmn_id), payload, format="json")


def payload(*points, **extra):
    return {
        "project_number": "1255",
        "event_date": "2026-11-01",
        "measuring_points": list(points),
        **extra,
    }


def test_url():
    assert url() == f"/api/uploadtasks/gmn/{GMN_ID}/comparison/"


# ------------------------------------------------------------------ two steps


@pytest.mark.django_db
def test_preview_creates_nothing(api_client, user, userprofile, bro, celery):
    login(api_client, user)

    response = post(api_client, payload(A, NEW_E))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "actions": [
            {
                "registration_type": "GMN_MeasuringPointEndDate",
                "measuring_point_code": "B",
                "event_date": "2026-11-01",
            },
            {
                "registration_type": "GMN_MeasuringPoint",
                "measuring_point_code": "E",
                "event_date": "2026-11-01",
                "new": {"bro_id": "GMW000000000006", "tube_number": 1},
            },
        ]
    }
    assert UploadTask.objects.count() == 0
    bro.assert_called_once_with(GMN_ID)


@pytest.mark.django_db
def test_confirm_creates_upload_tasks(
    api_client, user, userprofile, organisation, bro, celery
):
    login(api_client, user)
    moved_b = {**B, "bro_id": "GMW000000000009", "event_date": "2026-10-01"}

    response = post(api_client, payload(A, moved_b, NEW_E, confirm=True))

    assert response.status_code == status.HTTP_201_CREATED
    actions = response.json()["actions"]
    assert [action["registration_type"] for action in actions] == [
        "GMN_TubeReference",
        "GMN_MeasuringPoint",
    ]

    task = UploadTask.objects.get(uuid=actions[0]["uuid"])
    assert task.data_owner == organisation
    assert task.bro_domain == "GMN"
    assert task.project_number == "1255"
    assert task.registration_type == "GMN_TubeReference"
    assert task.request_type == "registration"
    assert task.metadata == {
        "requestReference": f"{GMN_ID}_GMN_TubeReference_B_2026-10-01",
        "deliveryAccountableParty": "12345678",
        "broId": GMN_ID,
        "qualityRegime": "IMBRO",
    }
    assert task.sourcedocument_data == {
        "eventDate": "2026-10-01",
        "measuringPointCode": "B",
        "broId": "GMW000000000009",
        "tubeNumber": 2,
    }
    assert celery.call_count == 2


@pytest.mark.django_db
def test_confirm_without_differences_creates_nothing(
    api_client, user, userprofile, bro, celery
):
    login(api_client, user)

    response = post(api_client, payload(A, B, confirm=True))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"actions": []}
    assert UploadTask.objects.count() == 0


@pytest.mark.django_db
def test_camel_case_is_accepted(api_client, user, userprofile, bro, celery):
    login(api_client, user)

    response = post(
        api_client,
        {
            "projectNumber": "1255",
            "measuringPoints": [
                {
                    "measuringPointCode": "A",
                    "broId": "GMW000000000001",
                    "tubeNumber": 1,
                },
                {"measuringPointCode": "B", "endDate": "2026-11-20"},
            ],
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["actions"][0]["event_date"] == "2026-11-20"


@pytest.mark.django_db
def test_today_is_the_dutch_date(api_client, user, userprofile, bro, celery):
    login(api_client, user)
    # 23:30 UTC on 27 November is already 28 November in the Netherlands.
    late_evening = datetime(2026, 11, 27, 23, 30, tzinfo=UTC)
    new_today = {**NEW_E, "event_date": "2026-11-28"}

    with mock.patch("django.utils.timezone.now", return_value=late_evening):
        response = post(
            api_client, {"project_number": "1255", "measuring_points": [A, new_today]}
        )

    assert response.status_code == status.HTTP_200_OK
    # B is left out, so it ends on the default date: today in the Netherlands.
    assert [
        (action["measuring_point_code"], action["event_date"])
        for action in response.json()["actions"]
    ] == [("B", "2026-11-28"), ("E", "2026-11-28")]


# --------------------------------------------------------------------- errors


@pytest.mark.django_db
def test_comparison_errors_give_400(api_client, user, userprofile, bro, celery):
    login(api_client, user)

    response = post(api_client, payload(A, A, B, confirm=True))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "errors": ["A: deze code staat meer dan één keer in de lijst."]
    }
    assert UploadTask.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "point",
    [
        {"measuring_point_code": "B"},
        {"measuring_point_code": "B", "bro_id": "GMW000000000003"},
        {**B, "end_date": "2026-11-20"},
        {**B, "bro_id": "GMW123"},
        {**B, "event_date": "2026-10"},
    ],
)
def test_wrong_measuring_point_gives_400(
    api_client, user, userprofile, bro, celery, point
):
    login(api_client, user)

    response = post(api_client, payload(A, point))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    bro.assert_not_called()


@pytest.mark.django_db
def test_invalid_gmn_id_gives_400(api_client, user, userprofile, bro, celery):
    login(api_client, user)

    response = post(api_client, payload(A, B), gmn_id="GMN123")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    bro.assert_not_called()


@pytest.mark.django_db
def test_unknown_gmn_gives_404(api_client, user, userprofile, bro, celery):
    login(api_client, user)
    bro.side_effect = ObjectNotFound()

    response = post(api_client, payload(A, B))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_bro_unavailable_gives_502(api_client, user, userprofile, bro, celery):
    login(api_client, user)
    bro.side_effect = BROUnavailable()

    response = post(api_client, payload(A, B))

    assert response.status_code == status.HTTP_502_BAD_GATEWAY


@pytest.mark.django_db
def test_login_required(api_client, bro, celery):
    response = post(api_client, payload(A, B))

    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.django_db
def test_user_without_organisation(api_client, user, bro, celery):
    login(api_client, user)

    response = post(api_client, payload(A, B))

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert UploadTask.objects.count() == 0


# ------------------------------------------------------------------------ xml


@pytest.mark.django_db
def test_created_tasks_render_with_existing_templates(
    api_client, user, userprofile, bro, celery
):
    login(api_client, user)
    moved_b = {**B, "bro_id": "GMW000000000009"}

    response = post(api_client, payload(moved_b, NEW_E, confirm=True))

    assert response.status_code == status.HTTP_201_CREATED
    for action in response.json()["actions"]:
        task = UploadTask.objects.get(uuid=action["uuid"])
        xml = XMLGenerator(
            registration_type=task.registration_type,
            request_type=task.request_type,
            metadata=task.metadata,
            sourcedocs_data=task.sourcedocument_data,
        ).create_xml_file()

        assert f"<measuringPointCode>{action['measuring_point_code']}<" in xml
        assert f"<brocom:broId>{GMN_ID}</brocom:broId>" in xml
