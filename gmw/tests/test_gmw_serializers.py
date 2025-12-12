import pytest

from api.tests import fixtures
from gmw import serializers

# this setup is chosen because ruff removes the fixture imports in other methods
organisation = fixtures.organisation
gmw = fixtures.gmw
tube = fixtures.tube
event = fixtures.event
gmn = fixtures.gmn
measuringpoint = fixtures.measuringpoint


@pytest.mark.django_db
def test_gmw_serialization(gmw):
    serializer = serializers.GMWSerializer(instance=gmw)
    assert serializer.data["bro_id"] == gmw.bro_id
    assert serializer.data["linked_gmns"] == []


@pytest.mark.django_db
def test_gmw_serialization_with_linked_gmns(gmw, gmn, measuringpoint):
    serializer = serializers.GMWSerializer(instance=gmw)
    assert measuringpoint.gmn.uuid in serializer.data["linked_gmns"]


@pytest.mark.django_db
def test_gmw_overview_serialization(gmw):
    serializer = serializers.GMWOverviewSerializer(instance=gmw)
    assert serializer.data["bro_id"] == gmw.bro_id


@pytest.mark.django_db
def test_monitoring_tube_serialization(gmw, tube):
    serializer = serializers.MonitoringTubeSerializer(instance=tube)
    assert serializer.data["tube_number"] == tube.tube_number
    assert serializer.data["gmw_bro_id"] == gmw.bro_id
    assert serializer.data["gmw_well_code"] == gmw.well_code
    assert serializer.data["linked_gmns"] == []


@pytest.mark.django_db
def test_monitoring_tube_with_linked_gmns(gmw, tube, gmn, measuringpoint):
    serializer = serializers.MonitoringTubeSerializer(instance=tube)
    assert serializer.data["tube_number"] == tube.tube_number
    assert serializer.data["gmw_bro_id"] == gmw.bro_id
    assert serializer.data["gmw_well_code"] == gmw.well_code
    assert serializer.data["linked_gmns"] == [gmn.uuid]


@pytest.mark.django_db
def test_event_serialization(gmw, event):
    serializer = serializers.EventSerializer(instance=event)
    assert serializer.data["event_name"] == event.event_name
    assert serializer.data["gmw_bro_id"] == gmw.bro_id
    assert serializer.data["gmw_well_code"] == gmw.well_code
