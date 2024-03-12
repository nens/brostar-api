import uuid

import pytest
from django.contrib.auth.models import User
from django.test import TestCase

from api import models as api_models


def test_organisation1():
    organisation = api_models.Organisation(name="Nieuwegein")
    assert str(organisation) == "Nieuwegein"
