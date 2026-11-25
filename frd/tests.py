import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from api.tests import fixtures
from gmw import models as gmw_models

organisation = fixtures.organisation
user = fixtures.user
userprofile = fixtures.userprofile
frd = fixtures.frd

TUBE_COUNT = 25
MAX_QUERIES = 15  # Must not grow with the number of monitoring tubes.


@pytest.fixture
def many_tubes(organisation):
    for i in range(TUBE_COUNT):
        gmw = gmw_models.GMW.objects.create(
            data_owner=organisation, bro_id=f"GMW9{i:08d}"
        )
        gmw_models.MonitoringTube.objects.create(
            data_owner=organisation, gmw=gmw, tube_number="1"
        )


@pytest.mark.django_db
def test_frd_list_browsable_api_does_not_load_all_tubes(
    user, userprofile, frd, many_tubes
):
    """The browsable API renders the filter form; it must not list every tube."""
    client = APIClient()
    client.force_authenticate(user=user)

    with CaptureQueriesContext(connection) as queries:
        response = client.get(reverse("api:frd:frd-list"), HTTP_ACCEPT="text/html")

    assert response.status_code == 200
    assert len(queries) <= MAX_QUERIES


@pytest.mark.django_db
def test_frd_admin_change_page_does_not_load_all_tubes(organisation, frd, many_tubes):
    """The admin change page must not render a dropdown with every tube."""
    admin_user = User.objects.create_superuser(
        username="admin", email="admin@example.com", password="admin"
    )
    client = Client()
    client.force_login(admin_user, backend="django.contrib.auth.backends.ModelBackend")

    with CaptureQueriesContext(connection) as queries:
        response = client.get(reverse("admin:frd_frd_change", args=[frd.pk]))

    assert response.status_code == 200
    assert len(queries) <= MAX_QUERIES
