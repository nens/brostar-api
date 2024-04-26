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
        data["lab_file"] = fp
        r = api_client.post(url, data, format="multipart")

    assert r.status_code == 201
