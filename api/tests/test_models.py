from api import models as api_models


def test_organisation1():
    organisation = api_models.Organisation(name="Nieuwegein")
    assert str(organisation) == "Nieuwegein"
