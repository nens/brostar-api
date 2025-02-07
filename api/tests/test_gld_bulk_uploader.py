import uuid

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from api import models as api_models
from api.bro_upload.gld_bulk_upload import GLDBulkUploader
from api.tests import fixtures

user = fixtures.user
organisation = fixtures.organisation  # imported, even though not used in this file, because required for userprofile fixture
userprofile = fixtures.userprofile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_gld_bulk_uploader_invalid_init():
    """Testing the init of the GLDBulkUploader."""
    with pytest.raises(ValidationError):
        GLDBulkUploader(
            bulk_upload_instance_uuid="test",
            measurement_tvp_file_uuid="test2",
        )

    with pytest.raises(api_models.BulkUpload.DoesNotExist):
        GLDBulkUploader(
            bulk_upload_instance_uuid=uuid.uuid4(),
            measurement_tvp_file_uuid=uuid.uuid4(),
        )
