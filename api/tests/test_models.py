import pytest

from api import models as api_models
from api.choices import REGISTRATION_TYPE_OPTIONS
from api.tests import fixtures
from gmn import models as gmn_models
from gmw import models as gmw_models

# this setup is chosen because ruff removes the fixture imports in other methods
organisation = fixtures.organisation
gmw = fixtures.gmw
gmn = fixtures.gmn
gar = fixtures.gar


@pytest.mark.django_db
def test_organisation_name(organisation):
    assert str(organisation) == "Nieuwegein"


@pytest.mark.django_db
def test_import_task_name(organisation):
    import_task = api_models.ImportTask(
        bro_domain="GMN",
        kvk_number="123456789",
        data_owner=organisation,
    )

    assert str(import_task) == "GMN import - Nieuwegein"


@pytest.mark.django_db
def test_import_task_save_method(organisation):
    import_task = api_models.ImportTask.objects.create(
        data_owner=organisation,
        bro_domain="gmn",
        kvk_number="12345678",
        status="",
    )
    import_task.save()
    import_task.refresh_from_db()
    assert api_models.ImportTask.objects.count() == 1


@pytest.mark.django_db
def test_upload_task_name(organisation):
    upload_task = api_models.UploadTask(
        bro_domain="GMN",
        data_owner=organisation,
        project_number="1",
        registration_type="GMN_StartRegistration",
        request_type="registration",
    )

    assert str(upload_task) == "Nieuwegein: GMN_StartRegistration (registration)"


@pytest.mark.django_db
def test_upload_task_registration_types(organisation):
    for registration_type_option in REGISTRATION_TYPE_OPTIONS:
        upload_task = api_models.UploadTask(
            bro_domain="GMW",
            data_owner=organisation,
            project_number="1",
            registration_type=registration_type_option,
            request_type="registration",
        )

        assert (
            str(upload_task) == f"Nieuwegein: {registration_type_option} (registration)"
        )


@pytest.mark.django_db
def test_gmn_name(gmn):
    assert str(gmn) == "GMN123456789"


@pytest.mark.django_db
def test_measuringpoint_name(organisation, gmn):
    measuringpoint = gmn_models.Measuringpoint(
        data_owner=organisation, gmn=gmn, measuringpoint_code="MP1234"
    )

    assert str(measuringpoint) == "MP1234"


@pytest.mark.django_db
def test_gmw_name(gmw):
    assert str(gmw) == "GMW123456789"


@pytest.mark.django_db
def test_gar_name(gar):
    assert str(gar) == "GMW987654321"


@pytest.mark.django_db
def test_monitoringtube_name(organisation, gmw):
    monitoring_tube = gmw_models.MonitoringTube(
        data_owner=organisation, gmw=gmw, tube_number="1"
    )

    assert str(monitoring_tube) == "GMW123456789-1"


@pytest.mark.django_db
def test_bulk_upload_name(organisation):
    bulk_upload_task = api_models.BulkUpload(
        data_owner=organisation,
        bulk_upload_type="GAR",
    )

    assert str(bulk_upload_task) == "Nieuwegein: Bulk upload GAR"
