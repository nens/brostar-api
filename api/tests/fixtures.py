import pytest

from api import models as api_models
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
    organisation.save()
    return organisation


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
def upload_task_valid_input_data(organisation):
    return {
        "data_owner": organisation,
        "bro_domain": "GMN",
        "project_number": "1",
        "registration_type": "GMN_StartRegistration",
        "request_type": "registration",
        "status": "PENDING",
        "metadata": {},
        "sourcedocument_data": {},
    }
