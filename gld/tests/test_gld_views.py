import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from api.models import Organisation
from api.tests import fixtures
from gld.models import GLD, Observation

user = fixtures.user
organisation = fixtures.organisation  # imported, even though not used in this file, because required for userprofile fixture
userprofile = fixtures.userprofile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_gld_set_list(api_client, user):
    """Test the UserViewSet listview"""

    api_client.force_authenticate(user=user)
    url = reverse("api:gld:gld-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK


class GLDViewTestCase(APITestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Nelen & Schuurmans")
        self.gld = GLD.objects.create(data_owner=self.organisation, bro_id="BRO123")
        # Create and authenticate a user
        self.user = self.client.force_authenticate(user=self._create_test_user())

    def _create_test_user(self):
        from django.contrib.auth.models import User

        return User.objects.create_user(
            username="testuser", email="test@gmail.com", password="testpassword"
        )

    def test_gld_list_view(self):
        url = reverse("api:gld:gld-list")  # Use the name defined in gld/urls.py
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_gld_detail_view(self):
    #     url = reverse("api:gld:gld-detail", kwargs={"uuid": self.gld.uuid})
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)


class ObservationViewTestCase(APITestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Nelen & Schuurmans")
        self.gld = GLD.objects.create(
            data_owner=self.organisation, bro_id="GLD000012234"
        )
        self.observation = Observation.objects.create(
            gld=self.gld, observation_id="OBS001", data_owner=self.organisation
        )
        # Create and authenticate a user
        self.user = self.client.force_authenticate(user=self._create_test_user())

    def _create_test_user(self):
        from django.contrib.auth.models import User

        return User.objects.create_user(
            username="testuser", email="test@gmail.com", password="testpassword"
        )

    def test_observation_list_view(self):
        url = reverse("api:gld:observation-list")  # Use the name defined in gld/urls.py
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_observation_detail_view(self):
    #     url = reverse(
    #         "api:gld:observation-detail", kwargs={"uuid": self.observation.uuid}
    #     )
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
