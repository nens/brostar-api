import pytest
from unittest.mock import patch
from api.bro_import import bulk_import, object_import
from api import models
import uuid


@pytest.fixture
def import_task_instance(django_db_setup):
    return models.ImportTask.objects.create(
        uuid=uuid.uuid4(),
        bro_domain="GMN",
        organisation=models.Organisation.objects.create(
            uuid=uuid.uuid4(), name="Test Organisation", kvk_number="12345678"
        ),
        status="PENDING",
        log="",
    )


@pytest.mark.django_db
def test_bulk_importer_init(import_task_instance):
    with patch("api.models.ImportTask.objects.get", return_value=import_task_instance):
        bulk_importer = bulk_import.BulkImporter(import_task_instance.uuid)
        assert bulk_importer.import_task_instance == import_task_instance
        assert bulk_importer.bro_domain == "GMN"
        assert bulk_importer.organisation == import_task_instance.organisation
        assert bulk_importer.kvk_number == "12345678"
        assert bulk_importer.object_importer == object_import.GMNObjectImporter
