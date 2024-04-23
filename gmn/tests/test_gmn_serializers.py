from datetime import date, datetime

import pytest

from api.tests import fixtures
from gmn import serializers

# this setup is chosen because ruff removes the fixture imports in other methods
organisation = fixtures.organisation
gmn = fixtures.gmn
gmw = fixtures.gmw


@pytest.mark.django_db
def test_gmn_serialization(gmn):
    serializer = serializers.GMNSerializer(instance=gmn)
    assert serializer.data["bro_id"] == gmn.bro_id


@pytest.mark.django_db
def test_gmn_deserialization(gmn, organisation):
    input_data = {
        "data_owner": organisation.uuid,
        "bro_id": "GMN123456789",
        "delivery_accountable_party": "12345678",
        "quality_regime": "IMBRO",
        "name": "test",
        "delivery_context": "test",
        "monitoring_purpose": "test",
        "groundwater_aspect": "test",
        "start_date_monitoring": date(2000, 1, 1),
        "object_registration_time": datetime(2000, 1, 1),
        "registration_status": "test",
        "color": "#000fff",
    }
    serializer = serializers.GMNSerializer(data=input_data)
    assert serializer.is_valid(), serializer.errors
