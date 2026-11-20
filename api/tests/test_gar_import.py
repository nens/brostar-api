import pytest
import xmltodict

from api.bro_import.object_import import GARObjectImporter
from api.models import Organisation
from api.tests.fixtures import organisation  # noqa: F401
from gar.models import GAR, Analysis

# Shortened GAR dispatch with fictional IDs, in the shape the BRO delivers it.
GAR_XML = """<?xml version="1.0" encoding="UTF-8"?>
<dispatchDataResponse xmlns="http://www.broservices.nl/xsd/dsgar/1.0"
    xmlns:gml="http://www.opengis.net/gml/3.2"
    xmlns:brocom="http://www.broservices.nl/xsd/brocommon/3.0"
    xmlns:garcommon="http://www.broservices.nl/xsd/garcommon/1.0">
  <dispatchDocument>
    <GAR_O gml:id="BRO_0002">
      <brocom:broId>GAR000000000001</brocom:broId>
      <brocom:deliveryAccountableParty>12345678</brocom:deliveryAccountableParty>
      <brocom:qualityRegime>IMBRO/A</brocom:qualityRegime>
      <qualityControlMethod codeSpace="urn:bro:gar:QualityControlMethod">onbekend</qualityControlMethod>
      <monitoringPoint>
        <garcommon:GroundwaterMonitoringTube gml:id="BRO_0001">
          <garcommon:broId>GMW000000000001</garcommon:broId>
          <garcommon:tubeNumber>1</garcommon:tubeNumber>
        </garcommon:GroundwaterMonitoringTube>
      </monitoringPoint>
      <fieldResearch>
        <garcommon:samplingDateTime>2007-11-15T11:00:00+01:00</garcommon:samplingDateTime>
        <garcommon:samplingStandard codeSpace="urn:bro:gar:SamplingStandard">onbekend</garcommon:samplingStandard>
        <garcommon:samplingDevice>
          <garcommon:pumpType codeSpace="urn:bro:gar:PumpType">onbekend</garcommon:pumpType>
        </garcommon:samplingDevice>
        <garcommon:fieldObservation>
          <garcommon:primaryColour codeSpace="urn:bro:gar:Colour">wit</garcommon:primaryColour>
          <garcommon:secondaryColour codeSpace="urn:bro:gar:Colour">grijs</garcommon:secondaryColour>
          <garcommon:colourStrength codeSpace="urn:bro:gar:ColourStrength">licht</garcommon:colourStrength>
          <garcommon:abnormalityInCooling>ja</garcommon:abnormalityInCooling>
          <garcommon:abnormalityInDevice>nee</garcommon:abnormalityInDevice>
          <garcommon:pollutedByEngine>onbekend</garcommon:pollutedByEngine>
          <garcommon:filterAerated>ja</garcommon:filterAerated>
          <garcommon:groundWaterLevelDroppedTooMuch>nee</garcommon:groundWaterLevelDroppedTooMuch>
          <garcommon:abnormalFilter>onbekend</garcommon:abnormalFilter>
          <garcommon:sampleAerated>ja</garcommon:sampleAerated>
          <garcommon:hoseReused>nee</garcommon:hoseReused>
          <garcommon:temperatureDifficultToMeasure>onbekend</garcommon:temperatureDifficultToMeasure>
        </garcommon:fieldObservation>
      </fieldResearch>
      <laboratoryAnalysis>
        <garcommon:analysisProcess>
          <garcommon:analysisDate><brocom:date>2007-11-15</brocom:date></garcommon:analysisDate>
          <garcommon:analyticalTechnique codeSpace="urn:bro:gar:AnalyticalTechnique">AAS</garcommon:analyticalTechnique>
          <garcommon:valuationMethod codeSpace="urn:bro:gar:ValuationMethod">CIW</garcommon:valuationMethod>
          <garcommon:analysis>
            <garcommon:parameter>1267</garcommon:parameter>
            <garcommon:analysisMeasurementValue uom="ug/l">8.7</garcommon:analysisMeasurementValue>
            <garcommon:reportingLimit uom="ug/l">8.7</garcommon:reportingLimit>
            <garcommon:qualityControlStatus codeSpace="urn:bro:gar:QualityControlStatus">onbeslist</garcommon:qualityControlStatus>
          </garcommon:analysis>
          <garcommon:analysis>
            <garcommon:parameter>284</garcommon:parameter>
            <garcommon:analysisMeasurementValue uom="ug/l">54</garcommon:analysisMeasurementValue>
            <garcommon:limitSymbol codeSpace="urn:bro:gar:LimitSymbol">LT</garcommon:limitSymbol>
            <garcommon:reportingLimit uom="ug/l">54</garcommon:reportingLimit>
            <garcommon:qualityControlStatus codeSpace="urn:bro:gar:QualityControlStatus">goedgekeurd</garcommon:qualityControlStatus>
          </garcommon:analysis>
        </garcommon:analysisProcess>
      </laboratoryAnalysis>
    </GAR_O>
  </dispatchDocument>
</dispatchDataResponse>
"""


def _analyses_by_parameter() -> dict[str, dict]:
    process = xmltodict.parse(GAR_XML)["dispatchDataResponse"]["dispatchDocument"][
        "GAR_O"
    ]["laboratoryAnalysis"]["garcommon:analysisProcess"]
    return {a["garcommon:parameter"]: a for a in process["garcommon:analysis"]}


def test_parse_analysis_keeps_value_and_reporting_limit():
    result = GARObjectImporter._parse_analysis(_analyses_by_parameter()["1267"])

    assert result == {
        "value": "8.7",
        "unit": "ug/l",
        "reporting_limit": "8.7",
        "limit_symbol": None,
        "status_quality_control": "onbeslist",
    }


def test_parse_analysis_keeps_value_with_limit_symbol():
    result = GARObjectImporter._parse_analysis(_analyses_by_parameter()["284"])

    assert result["value"] == "54"
    assert result["limit_symbol"] == "LT"
    assert result["reporting_limit"] == "54"


def test_parse_analysis_nil_value_takes_unit_from_reporting_limit():
    analysis = {
        "garcommon:parameter": "284",
        "garcommon:analysisMeasurementValue": {"@xsi:nil": "true"},
        "garcommon:limitSymbol": {
            "@codeSpace": "urn:bro:gar:LimitSymbol",
            "#text": "LT",
        },
        "garcommon:reportingLimit": {"@uom": "ug/l", "#text": "54"},
        "garcommon:qualityControlStatus": {"#text": "goedgekeurd"},
    }

    result = GARObjectImporter._parse_analysis(analysis)

    assert result["value"] is None
    assert result["unit"] == "ug/l"
    assert result["reporting_limit"] == "54"


@pytest.mark.django_db
def test_gar_import_saves_colours_and_analyses(organisation: Organisation):  # noqa: F811
    importer = GARObjectImporter("GAR000000000001", organisation)
    importer._save_data_to_database(xmltodict.parse(GAR_XML))

    gar = GAR.objects.get(bro_id="GAR000000000001")
    assert gar.primary_colour == "wit"
    assert gar.secondary_colour == "grijs"
    assert gar.colour_strength == "licht"

    lt_analysis = Analysis.objects.get(
        analysis_process__laboratory_research__gar=gar, parameter=284
    )
    assert lt_analysis.value == "54"
    assert lt_analysis.limit_symbol == "LT"
    assert lt_analysis.reporting_limit == "54"
