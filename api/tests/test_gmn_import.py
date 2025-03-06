import polars as pl
import pytest

from api.bro_import import object_import
from api.tests import fixtures

organisation = fixtures.organisation
importtask = fixtures.importtask


@pytest.mark.django_db
def test_init_gmn_importer():
    gmn_importer = object_import.GMNObjectImporter(
        bro_id="GMN00000111234", data_owner="me"
    )

    assert gmn_importer.bro_domain == "GMN"
    assert gmn_importer.bro_id == "GMN00000111234"
    assert gmn_importer.data_owner == "me"


@pytest.mark.django_db
def test_init_gmn_intermediate_events():
    gmn_importer = object_import.GMNObjectImporter(
        bro_id="GMN00000111234", data_owner="me"
    )

    dummy_xml_string = """
    <events>
        <intermediateEvent>
            <eventName codeSpace="urn:bro:gmn:EventName">meetpuntToevoegen</eventName>
            <eventDate>
                <brocom:date>1937-12-31</brocom:date>
            </eventDate>
            <measuringPointCode>GMW33G000083-001</measuringPointCode>
        </intermediateEvent>
        <intermediateEvent>
            <eventName codeSpace="urn:bro:gmn:EventName">meetpuntToevoegen</eventName>
            <eventDate>
                <brocom:date>1948-01-01</brocom:date>
            </eventDate>
            <measuringPointCode>GMW26H000039-002</measuringPointCode>
        </intermediateEvent>
    </events>
    """
    json_data = gmn_importer._convert_xml_to_json(dummy_xml_string)
    events_data = json_data.get("events", {}).get("intermediateEvent", [])
    gmn_importer._create_events_df(events_data)
    print(gmn_importer.events_df.row(0))
    assert isinstance(gmn_importer.events_df, pl.DataFrame)
    assert gmn_importer.events_df.row(0) == (
        "meetpuntToevoegen",
        "1937-12-31",
        "GMW33G000083-001",
    )
