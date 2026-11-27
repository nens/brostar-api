from pathlib import Path
from unittest import mock

import pytest
import requests

from api.comparisons.gmn import client
from api.comparisons.gmn.xml_reader import Tube, parse_gmn_response
from api.corrections.exceptions import BROUnavailable, ObjectNotFound

XML_DIR = Path(__file__).parent / "xml_strings"


def read_xml(name: str) -> str:
    return (XML_DIR / name).read_text(encoding="utf-8")


# ------------------------------------------------------------------ xml reader


def test_parse_gmn_metadata():
    gmn = parse_gmn_response(read_xml("GMN000000000703.xml"))

    assert gmn.bro_id == "GMN000000000703"
    assert gmn.delivery_accountable_party == "24493197"
    assert gmn.quality_regime == "IMBRO"
    assert gmn.start_date_monitoring == "2022-06-28"
    assert not gmn.ended
    assert len(gmn.measuring_points) == 48


def test_replaced_tube_gives_current_tube():
    gmn = parse_gmn_response(read_xml("GMN000000000703.xml"))

    point = gmn.measuring_points["GMP-R29"]
    assert point.tube == Tube(bro_id="GMW000000083218", tube_number=1)
    # The endDate of the old tube does not end the measuring point.
    assert point.is_active


def test_ended_gmn():
    gmn = parse_gmn_response(read_xml("GMN000000000081.xml"))

    assert gmn.ended
    assert gmn.end_date_monitoring == "2021-10-11"


def test_ended_measuring_points():
    gmn = parse_gmn_response(read_xml("gmn_comparison_ended_point.xml"))

    assert set(gmn.active_measuring_points) == {"A", "B"}
    assert gmn.measuring_points["C"].end_date == "2023-05-01"
    # Ended on an unknown date: still ended.
    assert gmn.measuring_points["D"].ended
    assert gmn.measuring_points["D"].end_date is None


def test_no_dispatch_document():
    with pytest.raises(ValueError):
        parse_gmn_response(
            '<dispatchDataResponse xmlns="http://www.broservices.nl/xsd/dsgmn/1.0"/>'
        )


# ---------------------------------------------------------------------- client


def response(status_code: int, text: str) -> mock.Mock:
    return mock.Mock(status_code=status_code, text=text)


def test_fetch_asks_for_full_history(monkeypatch):
    get = mock.Mock(return_value=response(200, "<xml/>"))
    monkeypatch.setattr(client.requests, "get", get)

    assert client.fetch_gmn_xml("GMN000000000703") == "<xml/>"
    assert get.call_args.kwargs["params"] == {"fullHistory": "ja"}
    assert get.call_args.args[0].endswith("/gm/gmn/v1/objects/GMN000000000703")


def test_fetch_unknown_gmn(monkeypatch):
    rejection = "<rejectionReason>Registratieobject GMN000000000002 bestaat niet.</rejectionReason>"
    monkeypatch.setattr(
        client.requests, "get", mock.Mock(return_value=response(400, rejection))
    )

    with pytest.raises(ObjectNotFound):
        client.fetch_gmn_xml("GMN000000000002")


@pytest.mark.parametrize("status_code", [400, 500, 503])
def test_fetch_bro_error(monkeypatch, status_code):
    monkeypatch.setattr(
        client.requests, "get", mock.Mock(return_value=response(status_code, "fout"))
    )

    with pytest.raises(BROUnavailable):
        client.fetch_gmn_xml("GMN000000000703")


def test_fetch_bro_unreachable(monkeypatch):
    monkeypatch.setattr(
        client.requests,
        "get",
        mock.Mock(side_effect=requests.ConnectionError("timeout")),
    )

    with pytest.raises(BROUnavailable):
        client.fetch_gmn_xml("GMN000000000703")
