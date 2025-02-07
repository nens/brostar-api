import polars as pl
import pytest

from api.bro_upload.gmn_bulk_upload import (
    _convert_and_check_df,
    check_date_string,
    determine_event_type,
)


def test_determine_event_type():
    assert "GMN_MeasuringPoint" == determine_event_type("meetpunt")
    assert "GMN_MeasuringPoint" == determine_event_type("toevoegenMP")
    assert "GMN_MeasuringPoint" == determine_event_type("ToevoegenMP")
    assert "GMN_MeasuringPoint" == determine_event_type("AddMonitoringPoint")
    assert "GMN_MeasuringPoint" == determine_event_type("AddMeasuringPoint")
    assert "GMN_MeasuringPointEndDate" == determine_event_type("end")
    assert "GMN_MeasuringPointEndDate" == determine_event_type("enddatum")
    assert "GMN_MeasuringPointEndDate" == determine_event_type("einddatum")
    assert "GMN_MeasuringPointEndDate" == determine_event_type("EndDate")
    assert "GMN_MeasuringPointEndDate" == determine_event_type("MeasuringPointEndDate")
    assert "GMN_MeasuringPointEndDate" == determine_event_type("meetpuntEindDatum")
    assert "GMN_TubeReference" == determine_event_type("referentie")
    assert "GMN_TubeReference" == determine_event_type("reference")
    assert "GMN_TubeReference" == determine_event_type("TubeReference")
    assert "GMN_TubeReference" == determine_event_type("BuisVerwijzing")
    assert "GMN_TubeReference" == determine_event_type("BuisReferentie")


def test_convert_and_check_df():
    df = pl.DataFrame(
        {
            "event": "gmn_event",
            "meetpuntcode": "gmn_123",
            "broid": "GMW123",
            "buis_nr": 1,
            "datum": "2025-01-01",
        }
    )
    df = _convert_and_check_df(df)

    assert df.columns == [
        "eventType",
        "measuringPointCode",
        "gmwBroId",
        "tubeNumber",
        "eventDate",
    ]


def test_check_date_string():
    with pytest.raises(ValueError):
        check_date_string("12-02-1999")

    with pytest.raises(ValueError):
        check_date_string("12-02")

    with pytest.raises(ValueError):
        check_date_string("120")

    assert check_date_string("1900-01-01") == "1900-01-01"
    assert check_date_string("1900-01") == "1900-01"
    assert check_date_string("1900") == "1900"
    assert check_date_string("") == ""
