import pytest
import pytz
from django.contrib.auth.models import User

from api import models as api_models
from gar import models as gar_models
from gld import models as gld_models
from gmn import models as gmn_models
from gmw import models as gmw_models

TZ_INFO = pytz.timezone("Europe/Amsterdam")


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
def organisation_user(organisation):
    _invite_user = api_models.InviteUser.objects.create(
        email="test@example.com",
        organisation=organisation,
    )
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
    return gmn_models.GMN.objects.create(
        data_owner=organisation,
        bro_id="GMN123456789",
        quality_regime="IMBRO/A",
        name="Test GMN",
    )


@pytest.fixture
def gmw(organisation):
    return gmw_models.GMW.objects.create(
        data_owner=organisation,
        bro_id="GMW123456789",
    )


@pytest.fixture
def gld(organisation):
    return gld_models.GLD.objects.create(
        data_owner=organisation,
        bro_id="GLD123456789",
        gmw_bro_id="GMW123456789",
        tube_number="1",
        quality_regime="IMBRO/A",
    )


@pytest.fixture
def gar(organisation):
    return gar_models.GAR.objects.create(
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


@pytest.fixture
def bulk_upload(organisation):
    return api_models.BulkUpload.objects.create(
        data_owner=organisation,
        project_number="1111",
        bulk_upload_type="GMN",
        request_type="registration",
        metadata={
            "broId": "GMN000001234",
            "projectNumber": "1111",
            "qualityRegime": "IMBRO/A",
            "requestReference": "GMN_MeasuringPoints_Bulk_BROSTAR_Request",
            "deliveryAccountableParty": "27376655",
        },
        sourcedocument_data={
            "name": "gmn",
            "deliveryContext": "kaderrichtlijnWater",
            "measuringPoints": [],
            "endDateMonitoring": "2025-01-12",
            "groundwaterAspect": "kwaliteit",
            "monitoringPurpose": "strategischBeheerKwaliteitLandelijk",
            "startDateMonitoring": "2025-01-10",
            "objectIdAccountableParty": "gmn",
        },
        status="PROCESSING",
        log="",
        progress=20.0,
    )
