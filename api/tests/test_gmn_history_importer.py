import json
from pathlib import Path

import pytest
from django.test import RequestFactory
from django.urls import reverse

from api.bro_import import gmn_history_importer as hi
from gmn.views import GMNHistoryView

BRO_ID = "GMN000000000703"
XML_PATH = Path(__file__).parent / "xml_strings" / f"{BRO_ID}.xml"


@pytest.fixture
def mock_bro(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.content = XML_PATH.read_bytes()
    return mocker.patch("requests.get", return_value=mock_response)


def test_history_importer_all_events_converted(mock_bro):
    result = hi.gmn_history_importer(BRO_ID)

    assert result["bro_id"] == BRO_ID
    assert result["number_of_events"] == 17
    assert all("sourcedocument" in event for event in result["events"])


def test_history_importer_tube_reference_uses_new_tube(mock_bro):
    result = hi.gmn_history_importer(BRO_ID)
    event = next(e for e in result["events"] if e["name"] == "monitoringbuisVervangen")

    assert event["sourcedocument"] == {
        "eventDate": "2024-06-04",
        "measuringPointCode": "GMP-R29",
        "broId": "GMW000000083218",
        "tubeNumber": 1,
    }


def test_history_importer_request_references_are_unique(mock_bro):
    result = hi.gmn_history_importer(BRO_ID)
    references = [e["metadata"]["requestReference"] for e in result["events"]]

    assert len(set(references)) == len(references)


def test_find_tube_no_match():
    measuring_points = [
        {
            "measuring_point_code": "MP1",
            "monitoring_tubes": [
                {
                    "bro_id": "GMW000000000001",
                    "tube_nr": "1",
                    "start_date": "2020-01-01",
                }
            ],
        }
    ]
    event = {
        "name": "meetpuntBeeindigen",
        "date": "2025-01-01",
        "measuring_point_code": "MP1",
    }

    assert hi.find_tube(measuring_points, event) is None


def test_measuring_point_end_date_extractor():
    event = {
        "name": "meetpuntBeeindigen",
        "date": "2025-09-15",
        "measuring_point_code": "PBGEER_1",
        "tube": None,
    }

    assert hi.measuring_point_end_date_extractor(event) == {
        "eventDate": "2025-09-15",
        "measuringPointCode": "PBGEER_1",
    }


def test_closure_extractor():
    event = {
        "name": "registratieBeeindigen",
        "date": "2025-12-31",
        "measuring_point_code": None,
        "tube": None,
    }

    assert hi.closure_extractor(event) == {"endDateMonitoring": "2025-12-31"}


def test_history_view_returns_json(mock_bro):
    request = RequestFactory().get(reverse("api:gmn:gmn-history", args=[BRO_ID]))
    response = GMNHistoryView.as_view()(request, gmn_id=BRO_ID)

    assert response.status_code == 200
    assert json.loads(response.content)["number_of_events"] == 17


def test_history_view_invalid_id():
    request = RequestFactory().get("/")
    response = GMNHistoryView.as_view()(request, gmn_id="GMN123")

    assert response.status_code == 500
    assert json.loads(response.content)["error"] == "Incorrect GMN-ID: GMN123"
