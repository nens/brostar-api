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


def test_host_redirect_view(api_client):
    """Test the localhost-redirect endpoint"""
    url = "/api/localhost-redirect"

    r = api_client.get(url)

    assert r.status_code == status.HTTP_302_FOUND


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
        "kvk": userprofile.organisation.kvk_number,
    }
    assert response.data == expected_data


@pytest.mark.django_db
def test_user_view_set_not_logged_in(api_client):
    """Test the logged_in action of UserViewSet with no logged in user"""
    url = reverse("api:user-logged-in")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK

    expected_data = {
        "logged_in": False,
        "login_url": "http://testserver/api-auth/login/",
        "logout_url": None,
        "user_id": None,
        "username": None,
        "first_name": None,
        "last_name": None,
        "email": None,
        "organisation": None,
        "kvk": None,
    }
    assert response.data == expected_data


@pytest.mark.django_db
def test_importtask_view_set_list_not_logged_in(api_client):
    """Test the importtask list endpoint"""
    url = "/api/importtasks/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


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

    assert response.status_code == status.HTTP_403_FORBIDDEN


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
        "sourcedocument_data": {},
        "data_owner": organisation.uuid,
    }

    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_uploadtask_view_post_invalid_data(api_client, user, userprofile, organisation):
    """Test posting on the uploadtasks enpoint
    Note: userprofile needs to be used as fixture for this test
    """
    api_client.force_authenticate(user=user)
    url = "/api/uploadtasks/"

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

    # Check 201 response for status = PENDING
    response = api_client.post(url)
    assert response.status_code == status.HTTP_201_CREATED

    # Check 303 response for status = PROCESSING
    upload_task_instance.status = "PROCESSING"
    upload_task_instance.save()

    response = api_client.post(url)
    assert response.status_code == status.HTTP_303_SEE_OTHER

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
