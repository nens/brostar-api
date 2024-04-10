import pytest

from api import models as api_models
from gmn import models as gmn_models
from gmw import models as gmw_models


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
def test_upload_task_save_method(organisation):
    upload_task = api_models.UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="gmn",
        project_number="1",
        status="PENDING",
        registration_type="GMN_StartRegistration",
        request_type="registration",
        metadata={},
        sourcedocument_data={},
    )
    upload_task.save()
    upload_task.refresh_from_db()
    assert api_models.UploadTask.objects.count() == 1


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
def test_monitoringtube_name(organisation, gmw):
    monitoring_tube = gmw_models.MonitoringTube(
        data_owner=organisation, gmw=gmw, tube_number="1"
    )

    assert str(monitoring_tube) == "GMW123456789-1"
