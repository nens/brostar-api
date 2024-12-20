import json
from unittest.mock import patch

import pandas as pd
import pytest
from rest_framework.test import APIClient

from api.tests import fixtures

user = fixtures.user
organisation = fixtures.organisation  # imported, even though not used in this file, because required for userprofile fixture
userprofile = fixtures.userprofile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_gld_bulk_upload_invalid_input(
    api_client, organisation, user, userprofile, tmp_path
):
    """Testing the 400 response on a request with just 1 file."""
    api_client.force_authenticate(user=user)
    url = "/api/bulkuploads/"

    data = {"bulk_upload_type": "GLD"}

    d = tmp_path / "sub"
    d.mkdir()
    file_path = d / "test.csv"
    csv_data = {"test1": ["test1", "test2"], "test2": ["test1", "test3"]}
    df = pd.DataFrame(csv_data)
    df.to_csv(file_path, index=False)

    with file_path.open("rb") as fp:
        data["measurements_tvp_file"] = fp
        r = api_client.post(url, data, format="multipart")

    assert r.status_code == 400


@pytest.mark.django_db
def test_gld_bulk_upload_valid_input(
    api_client, organisation, user, userprofile, tmp_path
):
    """Testing the 201 response on a valid request."""
    api_client.force_authenticate(user=user)
    url = "/api/bulkuploads/"

    d = tmp_path / "sub"
    d.mkdir()
    file_path = d / "test.csv"
    csv_data = {"test1": ["test1", "test2"], "test2": ["test1", "test3"]}
    df = pd.DataFrame(csv_data)
    df.to_csv(file_path, index=False)

    metadata_json = json.dumps(
        {
            "broId": "GLD000000076375",
            "projectNumber": "1889",
            "qualityRegime": "IMBRO",
            "requestReference": "test_request",
            "deliveryAccountableParty": "17278718",
        }
    )

    sourcedocument_json = json.dumps(
        {
            "investigatorKvk": "17278718",
            "observationType": "reguliereMeting",
            "processReference": "NEN5120v1991",
            "evaluationProcedure": "brabantWater2013",
            "statusQualityControl": "volledigBeoordeeld",
            "measurementInstrumentType": "druksensor",
            "airPressureCompensationType": "KNMImeting",
        }
    )

    with file_path.open("rb") as fp:
        data = {
            "bulk_upload_type": "GLD",
            "project_number": 1,
            "metadata": metadata_json,
            "sourcedocument_data": sourcedocument_json,
            "measurement_tvp_file": fp,
        }
        with patch("api.tasks.gld_bulk_upload_task.delay") as mock_task:
            r = api_client.post(url, data, format="multipart")

    assert mock_task.called
    assert r.status_code == 201
