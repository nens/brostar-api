from datetime import date, datetime

import pytest
from django.test import TestCase

from api.models import Organisation
from api.tests import fixtures
from gmn.models import GMN, IntermediateEvent, Measuringpoint
from gmn.serializers import (
    GMNSerializer,
    IntermediateEventSerializer,
    MeasuringpointSerializer,
)

# this setup is chosen because ruff removes the fixture imports in other methods
organisation = fixtures.organisation
gmn = fixtures.gmn
measuringpoint = fixtures.measuringpoint
intermediate_event = fixtures.intermediate_event
gmw = fixtures.gmw


@pytest.mark.django_db
def test_gmn_serialization(gmn):
    serializer = GMNSerializer(instance=gmn)
    assert serializer.data["bro_id"] == gmn.bro_id


@pytest.mark.django_db
def test_gmn_deserialization(gmn, organisation):
    input_data = {
        "data_owner": organisation.uuid,
        "bro_id": "GMN123456789",
        "internal_id": "TEST_GMN",
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
    serializer = GMNSerializer(data=input_data)
    assert serializer.is_valid(), serializer.errors


class GMNSerializerTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Nelen & Schuurmans")
        self.gmn = GMN.objects.create(
            data_owner=self.organisation, bro_id="GMN0000001234", name="dummy meetnet"
        )

    def test_serializer_data(self):
        serializer = GMNSerializer(self.gmn)
        self.assertIn("bro_id", serializer.data)
        self.assertIn("name", serializer.data)


class MeasuringPointSerializerTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Nelen & Schuurmans")
        self.gmn = GMN.objects.create(
            data_owner=self.organisation, bro_id="GMN0000001234"
        )
        self.measuring_point = Measuringpoint.objects.create(
            gmn=self.gmn,
            data_owner=self.gmn.data_owner,
            measuringpoint_code="dummy",
            gmw_bro_id="GMW0000001234",
            tube_number=3,
        )

    def test_serializer_data(self):
        serializer = MeasuringpointSerializer(self.measuring_point)
        self.assertIn("gmw_uuid", serializer.data)
        self.assertIn("monitoringtube_uuid", serializer.data)
        self.assertIn("location", serializer.data)


class EventSerializerTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Nelen & Schuurmans")
        self.gmn = GMN.objects.create(
            data_owner=self.organisation, bro_id="GMN0000001234"
        )
        self.event = IntermediateEvent.objects.create(
            gmn=self.gmn,
            data_owner=self.gmn.data_owner,
            event_type="GMN_MeasuringPoint",
            event_date=date(2025, 1, 1),
            measuringpoint_code="dummy",
            gmw_bro_id="GMW0000001234",
            tube_number=3,
        )

    def test_serializer_data(self):
        serializer = IntermediateEventSerializer(self.event)
        self.assertIn("event_type", serializer.data)
        self.assertIn("gmw_bro_id", serializer.data)
