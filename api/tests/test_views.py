from rest_framework import status
from rest_framework.test import APIClient
import pytest

@pytest.fixture
def api_client():
    return APIClient()

def test_host_redirect_view(api_client):
    """Test the localhost-redirect endpoint"""
    url = "/api/localhost-redirect"

    r = api_client.get(url)

    assert r.status_code == status.HTTP_302_FOUND