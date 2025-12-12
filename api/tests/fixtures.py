import datetime

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
def measuringpoint(organisation, gmn, gmw):
    return gmn_models.Measuringpoint.objects.create(
        data_owner=organisation,
        event_type="GMN_MeasuringPoint",
        measuringpoint_code="MP123456",
        gmn=gmn,
        gmw_bro_id=gmw.bro_id,
        tube_number="1",
    )


@pytest.fixture
def gmw(organisation):
    return gmw_models.GMW.objects.create(
        data_owner=organisation,
        bro_id="GMW123456789",
    )


@pytest.fixture
def tube(organisation, gmw):
    return gmw_models.MonitoringTube.objects.create(
        data_owner=organisation,
        gmw=gmw,
        tube_number="1",
        tube_top_diameter="50",
        sediment_sump_present="nee",
        artesian_well_cap_present="ja",
        tube_type="standaardbuis",
        tube_status="gebruiksklaar",
        tube_top_position="1.5",
        tube_top_positioning_method="AHN4",
        screen_top_position="-10.0",
        screen_bottom_position="-11.0",
        plain_tube_part_length="12.5",
        glue="geen",
        geo_ohm_cables=[],
        sock_material="nylon",
        tube_in_use="ja",
        tube_packing_material="bentonietFiltergrind",
        tube_material="pePvc",
    )


@pytest.fixture
def event(organisation, gmw):
    return gmw_models.Event.objects.create(
        data_owner=organisation,
        gmw=gmw,
        event_name="buisIngekort",
        event_date=datetime.date(2023, 1, 15),
        metadata={
            "broId": "GMW000000082117",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "27376655",
        },
        sourcedocument_data={
            "monitoringTubes": [
                {
                    "tubeNumber": "1",
                    "tubeTopPosition": "2.430",
                    "plainTubePartLength": "16.000",
                    "tubeTopPositioningMethod": "waterpassing0tot2cm",
                }
            ],
            "wellHeadProtector": "kokerMetaal",
        },
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
