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
def test_gar_bulk_upload_invalid_input(
    api_client, organisation, user, userprofile, tmp_path
):
    """Testing the 400 response on a request with just 1 file."""
    api_client.force_authenticate(user=user)
    url = "/api/bulkuploads/"

    data = {"bulk_upload_type": "GAR"}

    d = tmp_path / "sub"
    d.mkdir()
    file_path = d / "test.csv"
    csv_data = {"test1": ["test1", "test2"], "test2": ["test1", "test3"]}
    df = pd.DataFrame(csv_data)
    df.to_csv(file_path, index=False)

    with file_path.open("rb") as fp:
        data["fieldwork_file"] = fp
        r = api_client.post(url, data, format="multipart")

    assert r.status_code == 400


@pytest.mark.django_db
def test_gar_bulk_upload_valid_input(
    api_client, organisation, user, userprofile, tmp_path
):
    """Testing the 201 response on a valid request."""
    api_client.force_authenticate(user=user)
    url = "/api/bulkuploads/"

    d = tmp_path / "sub"
    d.mkdir()
    fieldwork_file_path = d / "fieldwork_test.csv"
    lab_file_path = d / "lab_test.csv"

    # Data for fieldwork file
    fieldwork_data = {"test1": ["test1", "test2"], "test2": ["test1", "test3"]}
    df_fieldwork = pd.DataFrame(fieldwork_data)
    df_fieldwork.to_csv(fieldwork_file_path, index=False)

    # Data for lab file
    lab_data = {"test3": ["test4", "test5"], "test4": ["test6", "test7"]}
    df_lab = pd.DataFrame(lab_data)
    df_lab.to_csv(lab_file_path, index=False)

    metadata_json = json.dumps(
        {
            "requestReference": "test",
            "qualityRegime": "IMBRO",
        }
    )

    with fieldwork_file_path.open("rb") as fp_fieldwork, lab_file_path.open(
        "rb"
    ) as fp_lab:
        data = {
            "bulk_upload_type": "GAR",
            "project_number": 1,
            "metadata": metadata_json,
            "fieldwork_file": fp_fieldwork,
            "lab_file": fp_lab,
        }
        with patch("api.tasks.gar_bulk_upload_task.delay") as mock_task:
            r = api_client.post(url, data, format="multipart")

    assert mock_task.called
    assert r.status_code == 201
