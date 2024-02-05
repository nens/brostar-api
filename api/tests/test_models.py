import pytest
import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from api import models


@pytest.mark.django_db
def test_user_create():
  User.objects.create_user('bro', 'bro@bro.bro', 'johnpassword')
  assert User.objects.count() == 1

@pytest.mark.django_db
def test_organisation_create():
    uuid_value = uuid.uuid4()
    name_value = 'organistation_test'
    kvk_number = '12345678'

    models.Organisation.objects.create(
        uuid=uuid_value,
        name=name_value,
        kvk_number=kvk_number
    )

    assert models.Organisation.objects.count() == 1


@pytest.mark.django_db
def test_user_profile_creation():
    # Create a User instance
    user = User.objects.create(username='testuser')

    # Create an Organisation instance
    organisation = models.Organisation.objects.create(
        uuid=uuid.uuid4(),
        name='Test Organisation',
        kvk_number='12345678'
    )

    # Create a UserProfile instance
    user_profile = models.UserProfile.objects.create(
        uuid=uuid.uuid4(),
        user=user,
        organisation=organisation
    )

    # Verify that the UserProfile instance is created successfully
    assert models.UserProfile.objects.count() == 1
    assert user_profile.uuid is not None
    assert user_profile.user == user
    assert user_profile.organisation == organisation


class ImportTaskModelTest(TestCase):

    def setUp(self):
        # Create an Organisation instance for testing
        self.organisation = models.Organisation.objects.create(
            uuid=uuid.uuid4(),
            name='Test Organisation',
            kvk_number='12345678'
        )

    def test_import_task_creation(self):
        # Create an ImportTask instance
        import_task = models.ImportTask.objects.create(
            uuid=uuid.uuid4(),
            bro_domain='GMN',
            organisation=self.organisation,
            status='PENDING',
            log='Test log entry'
        )

        # Verify that the ImportTask instance is created successfully
        self.assertEqual(models.ImportTask.objects.count(), 1)
        self.assertEqual(import_task.bro_domain, 'GMN')
        self.assertEqual(import_task.organisation, self.organisation)
        self.assertEqual(import_task.status, 'PENDING')
        self.assertEqual(import_task.log, 'Test log entry')

    def test_import_task_default_values(self):
        # Create an ImportTask instance without specifying some values
        import_task = models.ImportTask.objects.create(
            bro_domain='GMW',
            organisation=self.organisation
        )

        # Verify that default values are applied
        self.assertEqual(import_task.status, 'PENDING')

    def test_import_task_str_representation(self):
        # Create an ImportTask instance
        import_task = models.ImportTask.objects.create(
            bro_domain='GLD',
            organisation=self.organisation,
            status='COMPLETED'
        )

        # Verify the __str__ representation
        expected_str = f"GLD import - {self.organisation} ({import_task.created_at})"
        self.assertEqual(str(import_task), expected_str)