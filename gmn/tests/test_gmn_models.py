import pytest

from api.tests import fixtures

# Setup for ruff
organisation = fixtures.organisation
gmn = fixtures.gmn
measuringpoint = fixtures.measuringpoint
gmw = fixtures.gmw
intermediate_event = fixtures.intermediate_event


@pytest.mark.django_db
def test_intermediate_event_property(gmn, intermediate_event):
    assert intermediate_event.gmn_bro_id == gmn.bro_id


@pytest.mark.django_db
def test_intermediate_event__str__(intermediate_event):
    assert (
        intermediate_event.__str__()
        == f"{intermediate_event.measuringpoint_code}_{intermediate_event.event_type}_{intermediate_event.event_date}"
    )
