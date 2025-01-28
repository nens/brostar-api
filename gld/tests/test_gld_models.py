from django.test import TestCase

from api.models import Organisation  # Assuming Organisation exists in api.models
from gld.models import GLD, MeasurementTvp, Observation


class GLDModelTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Nelen & Schuurmans")
        self.gld = GLD.objects.create(
            data_owner=self.organisation,
            bro_id="GLD0000001234",
            delivery_accountable_party="16358291",
            quality_regime="IMBRO",
            gmw_bro_id="GMW0000021345",
            tube_number=1,
        )

    def test_gld_creation(self):
        self.assertEqual(self.gld.bro_id, "GLD0000001234")
        self.assertEqual(self.gld.nr_of_observations, 0)
        self.assertEqual(self.gld.tube_number, 1)
        self.assertEqual(self.gld.data_owner, self.organisation)
        self.assertEqual(self.gld.quality_regime, "IMBRO")


class ObservationModelTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Nelen & Schuurmans")
        self.gld = GLD.objects.create(
            data_owner=self.organisation, bro_id="GLD0000001234"
        )
        self.observation = Observation.objects.create(
            gld=self.gld,
            observation_id="OBS001",
            data_owner=self.organisation,
        )

    def test_observation_creation(self):
        self.assertEqual(self.observation.observation_id, "OBS001")
        self.assertEqual(self.observation.nr_of_measurements, 0)
        self.assertEqual(self.observation.gld, self.gld)
        self.assertEqual(self.gld.nr_of_observations, 1)


class MeasurementTvpModelTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Test Organisation")
        self.gld = GLD.objects.create(
            data_owner=self.organisation, bro_id="GLD0000001234"
        )
        self.observation = Observation.objects.create(
            gld=self.gld,
            observation_id="OBS001",
            data_owner=self.organisation,
        )
        self.measurement = MeasurementTvp.objects.create(
            observation=self.observation,
            time="2023-01-01T12:00:00Z",
            value=10.5,
            data_owner=self.organisation,
        )

    def test_measurement_creation(self):
        self.assertEqual(self.measurement.value, 10.5)
