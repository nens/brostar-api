from django.test import TestCase

from api.models import Organisation
from gld.models import GLD, MeasurementTvp, Observation
from gld.serializers import (
    GLDSerializer,
    MeasurementTvpSerializer,
    ObservationSerializer,
)


class GLDSerializerTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Nelen & Schuurmans")
        self.gld = GLD.objects.create(
            data_owner=self.organisation, bro_id="GLD0000001234"
        )

    def test_serializer_data(self):
        serializer = GLDSerializer(self.gld)
        self.assertIn("nr_of_observations", serializer.data)


class ObservationSerializerTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Nelen & Schuurmans")
        self.gld = GLD.objects.create(
            data_owner=self.organisation, bro_id="GLD0000001234"
        )
        self.observation = Observation.objects.create(
            gld=self.gld, observation_id="OBS001", data_owner=self.organisation
        )

    def test_serializer_data(self):
        serializer = ObservationSerializer(self.observation)
        self.assertIn("nr_of_measurements", serializer.data)
        self.assertEqual(serializer.data["nr_of_measurements"], 0)


class MeasurementTvpSerializerTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Nelen & Schuurmans")
        self.gld = GLD.objects.create(
            data_owner=self.organisation, bro_id="GLD0000001234"
        )
        self.observation = Observation.objects.create(
            gld=self.gld, observation_id="OBS001", data_owner=self.organisation
        )
        self.measurement = MeasurementTvp.objects.create(
            observation=self.observation,
            time="2023-01-01T12:00:00Z",
            value=10.5,
            data_owner=self.organisation,
        )

    def test_serializer_data(self):
        serializer = MeasurementTvpSerializer(self.measurement)
        self.assertIn("value", serializer.data)
        self.assertEqual(serializer.data["value"], 10.5)
        self.assertEqual(serializer.data["time"], "2023-01-01T12:00:00Z")
        self.assertEqual(serializer.data["data_owner"], self.organisation.uuid)
