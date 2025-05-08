from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api import models as api_models
from api.tests import fixtures

user = fixtures.user
organisation = fixtures.organisation  # imported, even though not used in this file, because required for userprofile fixture
userprofile = fixtures.userprofile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_user_view_set_list(api_client, user):
    """Test the UserViewSet listview"""

    api_client.force_authenticate(user=user)
    url = reverse("api:user-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_view_set_logged_in(api_client, user, userprofile):
    """Test the logged_in action of UserViewSet with a logged in user"""

    api_client.force_authenticate(user=user)

    url = reverse("api:user-logged-in")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK

    expected_data = {
        "logged_in": True,
        "login_url": None,
        "logout_url": "http://testserver/api-auth/logout/",
        "user_id": user.pk,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "organisation": userprofile.organisation.name,
        "organisation_url": f"http://testserver/api/organisations/{userprofile.organisation.uuid}",
        "kvk": userprofile.organisation.kvk_number,
        "organisation_current_request_count": 0,
        "bro_credentials_set": True,
    }
    assert response.data == expected_data


@pytest.mark.django_db
def test_user_view_set_not_logged_in(api_client):
    """Test the logged_in action of UserViewSet with no logged in user"""
    url = reverse("api:user-logged-in")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_organisation_list_logged_in(api_client, user):
    """Test the organisation list endpoint"""
    api_client.force_authenticate(user=user)
    url = "/api/organisations/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_organisation_list_not_logged_in(
    api_client,
):
    """Test the organisation list endpoint"""
    url = "/api/organisations/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_importtask_view_set_list_not_logged_in(api_client):
    """Test the importtask list endpoint"""
    url = "/api/importtasks/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_importtask_view_set_list_logged_in(api_client, user, userprofile):
    """Test the importtask list endpoint
    Note: userprofile needs to be used as fixture for this test
    """
    api_client.force_authenticate(user=user)
    url = "/api/importtasks/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_importtask_view_post_valid_data(api_client, user, userprofile, organisation):
    """Test posting on the importtask enpoint
    Note: userprofile needs to be used as fixture for this test
    """
    api_client.force_authenticate(user=user)
    url = "/api/importtasks/"

    data = {
        "bro_domain": "GMN",
        "kvk_number": organisation.kvk_number,
        "data_owner": organisation.uuid,
    }

    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_importtask_view_post_invalid_data(api_client, user, userprofile, organisation):
    """Test posting on the importtask enpoint
    Note: userprofile needs to be used as fixture for this test
    """
    api_client.force_authenticate(user=user)
    url = "/api/importtasks/"

    data = {
        "bro_domain": "non-existing",
        "kvk_number": organisation.kvk_number,
        "data_owner": organisation.uuid,
    }

    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_uploadtask_view_set_list_not_logged_in(api_client):
    """Test the uploadtask list endpoint"""
    url = "/api/uploadtasks/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_uploadtask_view_set_list_logged_in(api_client, user, userprofile):
    """Test the uploadtask list endpoint
    Note: userprofile needs to be used as fixture for this test
    """
    api_client.force_authenticate(user=user)
    url = "/api/uploadtasks/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_uploadtask_view_post_valid_data(api_client, user, userprofile, organisation):
    """Test posting on the uploadtask enpoint
    Note: userprofile needs to be used as fixture for this test
    """
    api_client.force_authenticate(user=user)
    url = "/api/uploadtasks/"

    data = {
        "bro_domain": "GMN",
        "project_number": "1",
        "registration_type": "GMN_StartRegistration",
        "request_type": "registration",
        "metadata": {
            "requestReference": "test",
            "deliveryAccountableParty": "12345678",
            "qualityRegime": "IMBRO",
        },
        "sourcedocument_data": {
            "objectIdAccountableParty": "test",
            "name": "test",
            "deliveryContext": "kaderrichtlijnWater",
            "monitoringPurpose": "strategischBeheerKwaliteitRegionaal",
            "groundwaterAspect": "kwantiteit",
            "startDateMonitoring": "2024-01-01",
            "measuringPoints": [
                {
                    "measuringPointCode": "GMW000000038946",
                    "broId": "GMW000000038946",
                    "tubeNumber": "1",
                }
            ],
        },
        "data_owner": organisation.uuid,
    }

    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED

    # Additional check to assert the returned data
    response_data = response.json()
    assert response_data["bro_domain"] == data["bro_domain"]
    assert response_data["project_number"] == data["project_number"]
    assert response_data["registration_type"] == data["registration_type"]
    assert response_data["request_type"] == data["request_type"]
    assert response_data["metadata"] == data["metadata"]
    assert response_data["sourcedocument_data"] == data["sourcedocument_data"]
    assert response_data["data_owner"] == str(organisation.uuid)


@pytest.mark.django_db
def test_uploadtask_view_post_valid_gld_addition_data(
    api_client, user, userprofile, organisation
):
    """Test posting on the uploadtask enpoint
    Note: userprofile needs to be used as fixture for this test
    """
    api_client.force_authenticate(user=user)
    url = "/api/uploadtasks/"

    data = {
        "bro_domain": "GLD",
        "project_number": "1",
        "registration_type": "GLD_Addition",
        "request_type": "registration",
        "metadata": {
            "requestReference": "test",
            "deliveryAccountableParty": "12345678",
            "qualityRegime": "IMBRO",
            "broId": "GLD00000001234",
        },
        "sourcedocument_data": {
            "beginPosition": "2021-01-19",
            "date": "2025-01-09",
            "endPosition": "2025-01-09",
            "investigatorKvk": "24483298",
            "observationType": "reguliereMeting",
            "processReference": "NPR_ISO.TR23211v2009",
            "evaluationProcedure": "oordeelDeskundig",
            "measurementInstrumentType": "drukSensor",
            "airPressureCompensationType": "knmimeting",
            "resultTime": "2025-01-09T09:52:00+01:00",
            "timeValuePairs": [
                {
                    "censorReason": None,
                    "censoringLimitvalue": None,
                    "statusQualityControl": "onbeslist",
                    "time": "2021-01-19T09:16:00+01:00",
                    "value": -1.8,
                },
                {
                    "censorReason": None,
                    "censoringLimitvalue": None,
                    "statusQualityControl": "onbeslist",
                    "time": "2021-02-04T09:55:00+01:00",
                    "value": -1.72,
                },
            ],
            "validationStatus": "voorlopig",
        },
        "data_owner": organisation.uuid,
    }

    response = api_client.post(url, data, format="json")
    print(response.json())
    assert response.status_code == status.HTTP_201_CREATED

    # Additional check to assert the returned data
    response_data = response.json()
    assert response_data["bro_domain"] == data["bro_domain"]
    assert response_data["project_number"] == data["project_number"]
    assert response_data["registration_type"] == data["registration_type"]
    assert response_data["request_type"] == data["request_type"]
    assert response_data["metadata"] == data["metadata"]
    assert isinstance(response_data["sourcedocument_data"]["observationId"], str)
    assert isinstance(
        response_data["sourcedocument_data"]["measurementTimeseriesId"], str
    )
    assert isinstance(response_data["sourcedocument_data"]["observationProcessId"], str)
    assert (
        response_data["sourcedocument_data"]["measurementInstrumentType"]
        == data["sourcedocument_data"]["measurementInstrumentType"]
    )
    assert (
        response_data["sourcedocument_data"]["timeValuePairs"]
        == data["sourcedocument_data"]["timeValuePairs"]
    )
    assert response_data["data_owner"] == str(organisation.uuid)


@pytest.mark.django_db
def test_uploadtask_view_post_invalid_data(api_client, user, userprofile, organisation):
    """Test posting on the uploadtasks enpoint
    Note: userprofile needs to be used as fixture for this test
    """
    api_client.force_authenticate(user=user)
    url = "/api/uploadtasks/"

    # test the serializer check
    data = {
        "bro_domain": "non-existing",
        "project_number": "1",
        "registration_type": "GMN_StartRegistration",
        "request_type": "non-existing",
        "metadata": {},
        "sourcedocument_data": {},
        "data_owner": organisation.uuid,
    }

    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Test the pydantic model validation by sending an incomplete metadata
    data = {
        "bro_domain": "non-existing",
        "project_number": "1",
        "registration_type": "GMN_StartRegistration",
        "request_type": "GMN_StartRegistration",
        "metadata": {
            "requestReference": "test",
            "deliveryAccountableParty": "12345678",
        },
        "sourcedocument_data": {},
        "data_owner": organisation.uuid,
    }

    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@patch("api.bro_upload.utils.check_delivery_status")
def test_uploadtask_check_status(
    mock_check_delivery_status, api_client, user, userprofile, organisation
):
    """Test post on uploadtasks/check-status endpoint
    Note: userprofile needs to be used as fixture for this test
    """
    api_client.force_authenticate(user=user)

    upload_task_instance = api_models.UploadTask.objects.create(
        bro_domain="GMN",
        project_number="1",
        registration_type="GMN_StartRegistration",
        request_type="registration",
        metadata={},
        sourcedocument_data={},
        data_owner=organisation,
        status="PENDING",
    )

    url = reverse(
        "api:uploadtask-check-status", kwargs={"uuid": upload_task_instance.uuid}
    )

    # Check 303 response for status = PROCESSING
    response = api_client.post(url)
    assert response.status_code == status.HTTP_303_SEE_OTHER

    # SHOULD NEVER REMAIN ON PENDING AS POST SAVE SHOULD THEN SET IT TO PROCESSING AND START A TASK.

    # Check 303 response for status = COMPLETED
    upload_task_instance.status = "COMPLETED"
    upload_task_instance.save()

    response = api_client.post(url)
    assert response.status_code == status.HTTP_303_SEE_OTHER

    # Check 303 response for status = FAILED
    upload_task_instance.status = "FAILED"
    upload_task_instance.save()

    response = api_client.post(url)
    assert response.status_code == status.HTTP_303_SEE_OTHER

    # Check 303 response for status = UNFINISHED -> FAILED
    upload_task_instance.status = "UNFINISHED"
    upload_task_instance.save()

    mock_check_delivery_status.return_value = {
        "brondocuments": [
            {
                "errors": ["ERROR!!!"],
                "status": "OPGENOMEN_LVBRO",
                "broId": "GMN1234",
            }
        ],
        "status": "DOORGELEVERD",
    }

    response = api_client.post(url)
    assert response.status_code == status.HTTP_303_SEE_OTHER

    # Check 200 response for status = UNFINISHED -> FINISHED
    mock_check_delivery_status.return_value = {
        "brondocuments": [
            {
                "errors": [],
                "status": "OPGENOMEN_LVBRO",
                "broId": "GMN1234",
            }
        ],
        "status": "DOORGELEVERD",
    }

    response = api_client.post(url)
    assert response.status_code == status.HTTP_200_OK

    # Check 200 response for status = UNFINISHED -> UNFINISHED
    mock_check_delivery_status.return_value = {
        "brondocuments": [
            {
                "errors": [],
                "status": "NOTFINISHEDYET",
                "broId": "GMN1234",
            }
        ],
        "status": "DOORGELEVERD",
    }

    response = api_client.post(url)
    assert response.status_code == status.HTTP_304_NOT_MODIFIED
