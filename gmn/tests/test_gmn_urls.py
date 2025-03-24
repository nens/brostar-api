import uuid

from django.urls import reverse


def test_url_resolves():
    url = reverse("api:gmn:gmn-list")
    assert url == "/api/gmn/gmns/"

    test_uuid = uuid.uuid4()
    url = reverse("api:gmn:gmn-detail", kwargs={"uuid": test_uuid})
    assert url == f"/api/gmn/gmns/{test_uuid}/"

    url = reverse("api:gmn:measuringpoint-list")
    assert url == "/api/gmn/measuringpoints/"

    test_uuid = uuid.uuid4()
    url = reverse("api:gmn:measuringpoint-detail", kwargs={"uuid": test_uuid})
    assert url == f"/api/gmn/measuringpoints/{test_uuid}/"

    url = reverse("api:gmn:intermediateevent-list")
    assert url == "/api/gmn/events/"

    test_uuid = uuid.uuid4()
    url = reverse("api:gmn:intermediateevent-detail", kwargs={"uuid": test_uuid})
    assert url == f"/api/gmn/events/{test_uuid}/"
