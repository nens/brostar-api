import pytest
from django.contrib.auth.models import User

from api import models as api_models
from gar import models as gar_models
from gmn import models as gmn_models
from gmw import models as gmw_models


@pytest.fixture
def organisation():
    organisation = api_models.Organisation.objects.create(
        name="Nieuwegein",
        kvk_number="12345678",
        bro_user_token="secret",
        bro_user_password="secret",
    )
    return organisation


@pytest.fixture
def user():
    user = User.objects.create_user(
        username="test_user", email="test@example.com", password="test_password"
    )
    return user


@pytest.fixture
def userprofile(user, organisation):
    userprofile = api_models.UserProfile.objects.get(
        user=user,
    )
    userprofile.organisation = organisation
    userprofile.save()
    return userprofile


@pytest.fixture
def gmn(organisation):
    return gmn_models.GMN(
        data_owner=organisation,
        bro_id="GMN123456789",
    )


@pytest.fixture
def gmw(organisation):
    return gmw_models.GMW(
        data_owner=organisation,
        bro_id="GMW123456789",
    )


@pytest.fixture
def gar(organisation):
    return gar_models.GAR(
        data_owner=organisation,
        bro_id="GMW987654321",
    )


@pytest.fixture
def importtask(organisation):
    return api_models.ImportTask.objects.create(
        data_owner=organisation,
        bro_domain="GMN",
        kvk_number=organisation.kvk_number,
        status="PENDING",
    )
