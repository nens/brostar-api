import polars as pl
import pytest

from api.bro_import import object_import
from api.tests import fixtures

organisation = fixtures.organisation
gmn = fixtures.gmn
importtask = fixtures.importtask


@pytest.mark.django_db
def test_init_gmn_importer(organisation):
    gmn_importer = object_import.GMNObjectImporter(
        bro_id="GMN00000111234", data_owner=organisation
    )

    assert gmn_importer.bro_domain == "GMN"
    assert gmn_importer.bro_id == "GMN00000111234"
    assert gmn_importer.data_owner == organisation


@pytest.mark.django_db
def test_init_gmn_intermediate_events(organisation):
    gmn_importer = object_import.GMNObjectImporter(
        bro_id="GMN00000111234", data_owner=organisation
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


@pytest.mark.django_db
def test_init_gmn_measuring_points(gmn, organisation):
    gmn_importer = object_import.GMNObjectImporter(
        bro_id=gmn.bro_id, data_owner=organisation
    )
    gmn_importer.gmn_obj = gmn

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
    measuring_points_string = """
    <measuringPoints>
        <measuringPoint>
          <MeasuringPoint gml:id="BRO_2220">
            <measuringPointCode>GMW33G000083-001</measuringPointCode>
            <startDate>
              <brocom:date>1937-12-31</brocom:date>
            </startDate>
            <monitoringTube>
              <GroundwaterMonitoringTube gml:id="BRO_2219">
                <broId>GMW000000082554</broId>
                <tubeNumber>1</tubeNumber>
                <startDate>
                  <brocom:date>1937-12-31</brocom:date>
                </startDate>
              </GroundwaterMonitoringTube>
            </monitoringTube>
          </MeasuringPoint>
        </measuringPoint>
        <measuringPoint>
          <MeasuringPoint gml:id="BRO_2222">
            <measuringPointCode>GMW26H000039-002</measuringPointCode>
            <startDate>
              <brocom:date>1948-01-01</brocom:date>
            </startDate>
            <monitoringTube>
              <GroundwaterMonitoringTube gml:id="BRO_2221">
                <broId>GMW000000082506</broId>
                <tubeNumber>2</tubeNumber>
                <startDate>
                  <brocom:date>1948-01-01</brocom:date>
                </startDate>
              </GroundwaterMonitoringTube>
            </monitoringTube>
          </MeasuringPoint>
        </measuringPoint>
        <measuringPoint>
          <MeasuringPoint gml:id="BRO_2224">
            <measuringPointCode>GMW26G001789-001</measuringPointCode>
            <startDate>
              <brocom:date>2009-11-20</brocom:date>
            </startDate>
            <monitoringTube>
              <GroundwaterMonitoringTube gml:id="BRO_2223">
                <broId>GMW000000080971</broId>
                <tubeNumber>1</tubeNumber>
                <startDate>
                  <brocom:date>2009-11-20</brocom:date>
                </startDate>
              </GroundwaterMonitoringTube>
            </monitoringTube>
          </MeasuringPoint>
        </measuringPoint>
    </measuringPoints>
    """

    json_data = gmn_importer._convert_xml_to_json(dummy_xml_string)
    measuring_points_json = gmn_importer._convert_xml_to_json(measuring_points_string)
    events_data = json_data.get("events", {}).get("intermediateEvent", [])
    measuring_points_data = measuring_points_json.get("measuringPoints", {}).get(
        "measuringPoint", []
    )
    gmn_importer._create_events_df(events_data)
    gmn_importer._save_measuringpoint_data(measuring_points_data)
