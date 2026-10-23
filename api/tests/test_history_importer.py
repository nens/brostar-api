import json
from pathlib import Path

import pytest
from django.test import RequestFactory
from django.urls import reverse

from api.bro_import import history_importer as hi
from gmw.views import GMWHistoryView

BRO_ID = "GMW000000048905"
XML_PATH = Path(__file__).parent / "xml_strings" / f"{BRO_ID}.xml"


@pytest.fixture
def mock_bro(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.content = XML_PATH.read_bytes()
    return mocker.patch("requests.get", return_value=mock_response)


def test_history_importer_all_events_converted(mock_bro):
    result = hi.history_importer(BRO_ID)

    assert result["bro_id"] == BRO_ID
    assert result["number_of_events"] == 6
    assert all("sourcedocument" in event for event in result["events"])


def test_history_importer_metadata(mock_bro):
    result = hi.history_importer(BRO_ID)
    metadata = result["events"][0]["metadata"]

    assert metadata["requestReference"] == f"{BRO_ID}_nieuweInmetingPosities_2011-12-06"
    assert metadata["deliveryAccountableParty"] == "27375169"
    assert metadata["qualityRegime"] == "IMBRO/A"


def test_history_importer_maintainer_gets_default(mock_bro):
    result = hi.history_importer(BRO_ID)
    maintainer_event = next(
        e for e in result["events"] if e["eventName"] == "onderhouderVeranderd"
    )

    assert maintainer_event["sourcedocument"] == {
        "eventDate": "2020-01-01",
        "maintenanceResponsibleParty": hi.UNKNOWN_PARTY,
    }


def test_owner_extractor_gets_default():
    event = {
        "eventName": "eigenaarVeranderd",
        "eventDate": "2020-01-01",
        "wellData": {},
    }

    assert hi.owner_extractor(event) == {
        "eventDate": "2020-01-01",
        "owner": hi.UNKNOWN_PARTY,
    }


def test_history_view_returns_json(mock_bro):
    request = RequestFactory().get(reverse("api:gmw:gmw-history", args=[BRO_ID]))
    response = GMWHistoryView.as_view()(request, gmw_id=BRO_ID)

    assert response.status_code == 200
    assert json.loads(response.content)["number_of_events"] == 6


def test_history_view_invalid_id():
    request = RequestFactory().get("/")
    response = GMWHistoryView.as_view()(request, gmw_id="GMW123")

    assert response.status_code == 500
    assert json.loads(response.content)["error"] == "Incorrect GMW-ID: GMW123"
