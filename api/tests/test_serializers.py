import uuid
from django.test import TestCase
from api import models
from api import serializers


class ImportTaskSerializerTest(TestCase):
    def setUp(self):
        # Create an Organisation instance for testing
        self.organisation = models.Organisation.objects.create(
            uuid=uuid.uuid4(), name="Test Organisation", kvk_number="12345678"
        )

        # Create an ImportTask instance for testing
        self.import_task_data = {
            "uuid": uuid.uuid4(),
            "bro_domain": "GMN",
            "organisation": self.organisation.uuid,
            "status": "PENDING",
            "log": "Test log entry",
        }

    def test_import_task_serializer_valid_data(self):
        serializer = serializers.ImportTaskSerializer(data=self.import_task_data)

        # Check that the serializer is valid
        self.assertTrue(serializer.is_valid())

        # Check that the serializer saves the data correctly
        import_task_instance = serializer.save()
        self.assertEqual(import_task_instance.bro_domain, "GMN")
        self.assertEqual(import_task_instance.organisation, self.organisation)
        self.assertEqual(import_task_instance.status, "PENDING")
        self.assertEqual(import_task_instance.log, "Test log entry")

    def test_import_task_serializer_invalid_data(self):
        # Create invalid data (wrong BRO Domain)
        invalid_data = {
            "bro_domain": "GMWADFASd",
            "status": "PENDING",
            "log": "Test log entry",
        }

        serializer = serializers.ImportTaskSerializer(data=invalid_data)

        # Check that the serializer is not valid
        self.assertFalse(serializer.is_valid())
