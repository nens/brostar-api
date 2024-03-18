import pytest

from api import models as api_models
from gmn import models as gmn_models
from gmw import models as gmw_models


@pytest.fixture
def organisation():
    return api_models.Organisation(name="Nieuwegein")


def test_organisation_name(organisation):
    assert str(organisation) == "Nieuwegein"


def test_import_task_name(organisation):
    import_task = api_models.ImportTask(
        bro_domain="GMN",
        kvk_number="123456789",
        data_owner=organisation,
    )

    assert str(import_task) == "GMN import - Nieuwegein"


def test_upload_task_name(organisation):
    upload_task = api_models.UploadTask(
        bro_domain="GMN",
        data_owner=organisation,
        project_number="1",
        registration_type="GMN_StartRegistration",
        request_type="registration",
    )

    assert str(upload_task) == "Nieuwegein: GMN_StartRegistration (registration)"


@pytest.fixture
def gmn(organisation):
    return gmn_models.GMN(
        data_owner=organisation,
        bro_id="GMN123456789",
    )


def test_gmn_name(gmn):
    assert str(gmn) == "GMN123456789"


def test_measuringpoint_name(organisation, gmn):
    measuringpoint = gmn_models.Measuringpoint(
        data_owner=organisation, gmn=gmn, measuringpoint_code="MP1234"
    )

    assert str(measuringpoint) == "MP1234"


@pytest.fixture
def gmw(organisation):
    return gmw_models.GMW(
        data_owner=organisation,
        bro_id="GMW123456789",
    )


def test_gmw_name(gmw):
    assert str(gmw) == "GMW123456789"


def test_monitoringtube_name(organisation, gmw):
    monitoring_tube = gmw_models.MonitoringTube(
        data_owner=organisation, gmw=gmw, tube_number="1"
    )

    assert str(monitoring_tube) == "GMW123456789-1"
