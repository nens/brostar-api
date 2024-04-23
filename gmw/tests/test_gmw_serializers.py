import pytest

from api.tests import fixtures
from gmw import serializers

# this setup is chosen because ruff removes the fixture imports in other methods
organisation = fixtures.organisation
gmw = fixtures.gmw


@pytest.mark.django_db
def test_gmw_serialization(gmw):
    serializer = serializers.GMWSerializer(instance=gmw)
    assert serializer.data["bro_id"] == gmw.bro_id
