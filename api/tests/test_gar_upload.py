from api.bro_upload import object_upload

expected_gar_xml_str = """<registrationRequest xmlns="http://www.broservices.nl/xsd/isgar/1.0"
    xmlns:garcom="http://www.broservices.nl/xsd/garcommon/1.0"
    xmlns:brocom="http://www.broservices.nl/xsd/brocommon/3.0"
    xmlns:gml="http://www.opengis.net/gml/3.2"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.broservices.nl/xsd/isgar/1.0 https://schema.broservices.nl/xsd/isgar/1.0/isgar-messages.xsd">
    <brocom:requestReference>test</brocom:requestReference>

    <brocom:deliveryAccountableParty>test</brocom:deliveryAccountableParty>

    <brocom:qualityRegime>IMBRO</brocom:qualityRegime>

    <brocom:underPrivilege>ja</brocom:underPrivilege>

    <sourceDocument>
        <GAR gml:id="id_0001">
            <objectIdAccountableParty>test</objectIdAccountableParty>
            <qualityControlMethod codeSpace="urn:bro:gar:QualityControlMethod">handboekProvinciesRIVMv2017</qualityControlMethod>

            <groundwaterMonitoringNet>
                <garcom:GroundwaterMonitoringNet gml:id="GMN1234567890">
                    <garcom:broId>GMN1234567890</garcom:broId>
                </garcom:GroundwaterMonitoringNet>
            </groundwaterMonitoringNet>

            <monitoringPoint>
                <garcom:GroundwaterMonitoringTube gml:id="GMW1234567890_1">
                    <garcom:broId>GMW1234567890</garcom:broId>
                    <garcom:tubeNumber>1</garcom:tubeNumber>
                </garcom:GroundwaterMonitoringTube>
            </monitoringPoint>
            <fieldResearch>
                <garcom:samplingDateTime>2018-10-23T16:59:32+01:00</garcom:samplingDateTime>
                <garcom:samplingOperator>
                        <brocom:chamberOfCommerceNumber>123456789</brocom:chamberOfCommerceNumber>
                </garcom:samplingOperator>
                <garcom:samplingStandard codeSpace="urn:bro:gar:SamplingStandard">NEN5744v2011-A1v2013</garcom:samplingStandard>
                <garcom:samplingDevice>
                    <garcom:pumpType codeSpace="urn:bro:gar:PumpType">test</garcom:pumpType>
                </garcom:samplingDevice>
                <garcom:fieldObservation>

                    <garcom:primaryColour codeSpace="urn:bro:gar:Colour">test</garcom:primaryColour>


                    <garcom:secondaryColour codeSpace="urn:bro:gar:Colour">test</garcom:secondaryColour>


                    <garcom:abnormalityInCooling>test</garcom:abnormalityInCooling>
                    <garcom:abnormalityInDevice>test</garcom:abnormalityInDevice>
                    <garcom:pollutedByEngine>test</garcom:pollutedByEngine>
                    <garcom:filterAerated>test</garcom:filterAerated>
                    <garcom:groundWaterLevelDroppedTooMuch>test</garcom:groundWaterLevelDroppedTooMuch>
                    <garcom:abnormalFilter>test</garcom:abnormalFilter>
                    <garcom:sampleAerated>test</garcom:sampleAerated>
                    <garcom:hoseReused>test</garcom:hoseReused>
                    <garcom:temperatureDifficultToMeasure>test</garcom:temperatureDifficultToMeasure>
                </garcom:fieldObservation>

                <garcom:fieldMeasurement>
                    <garcom:parameter>1234</garcom:parameter>
                    <garcom:fieldMeasurementValue uom="m/s">3.0</garcom:fieldMeasurementValue>
                    <garcom:qualityControlStatus codeSpace="urn:bro:gar:QualityControlStatus">goed</garcom:qualityControlStatus>
                </garcom:fieldMeasurement>

            </fieldResearch>


            <laboratoryAnalysis>

                <garcom:responsibleLaboratory>
                        <brocom:chamberOfCommerceNumber>123456789</brocom:chamberOfCommerceNumber>
                </garcom:responsibleLaboratory>


                <garcom:analysisProcess>
                    <garcom:analysisDate>
                        <brocom:date>2018-10-25</brocom:date>
                    </garcom:analysisDate>
                    <garcom:analyticalTechnique codeSpace="urn:bro:gar:AnalyticalTechnique">AAS</garcom:analyticalTechnique>
                    <garcom:valuationMethod codeSpace="urn:bro:gar:ValuationMethod">CIW</garcom:valuationMethod>

                    <garcom:analysis>
                        <garcom:parameter>1234</garcom:parameter>
                        <garcom:analysisMeasurementValue uom="m/s">0.1</garcom:analysisMeasurementValue>

                        <garcom:limitSymbol codeSpace="urn:bro:gar:LimitSymbol">LT</garcom:limitSymbol>


                        <garcom:reportingLimit uom="m/s">1</garcom:reportingLimit>

                        <garcom:qualityControlStatus codeSpace="urn:bro:gar:QualityControlStatus">goed</garcom:qualityControlStatus>
                    </garcom:analysis>

                </garcom:analysisProcess>

            </laboratoryAnalysis>


        </GAR>
    </sourceDocument>
</registrationRequest>
"""


def test_gar_xml_creation():
    generator = object_upload.XMLGenerator(
        registration_type="GAR",
        request_type="registration",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
            "underPrivilege": "ja",
        },
        sourcedocs_data={
            "objectIdAccountableParty": "test",
            "qualityControlMethod": "handboekProvinciesRIVMv2017",
            "groundwaterMonitoringNets": [
                "GMN1234567890",
            ],
            "gmwBroId": "GMW1234567890",
            "tubeNumber": 1,
            "fieldResearch": {
                "samplingDateTime": "2018-10-23T16:59:32+01:00",
                "samplingOperator": "123456789",
                "samplingStandard": "NEN5744v2011-A1v2013",
                "pumpType": "test",
                "primaryColour": "test",
                "secondaryColour": "test",
                "abnormalityInCooling": "test",
                "abnormalityInDevice": "test",
                "pollutedByEngine": "test",
                "filterAerated": "test",
                "groundWaterLevelDroppedTooMuch": "test",
                "abnormalFilter": "test",
                "sampleAerated": "test",
                "hoseReused": "test",
                "temperatureDifficultToMeasure": "test",
                "fieldMeasurements": [
                    {
                        "parameter": 1234,
                        "unit": "m/s",
                        "fieldMeasurementValue": 3.0,
                        "qualityControlStatus": "goed",
                    },
                ],
            },
            "laboratoryAnalyses": [
                {
                    "responsibleLaboratoryKvk": "123456789",
                    "analysisProcesses": [
                        {
                            "date": "2018-10-25",
                            "analyticalTechnique": "AAS",
                            "valuationMethod": "CIW",
                            "analyses": [
                                {
                                    "parameter": "1234",
                                    "unit": "m/s",
                                    "analysisMeasurementValue": "0.1",
                                    "limitSymbol": "LT",
                                    "reportingLimit": "1",
                                    "qualityControlStatus": "goed",
                                },
                            ],
                        },
                    ],
                },
            ],
        },
    )

    xml = generator.create_xml_file()
    print(xml)
    assert xml == expected_gar_xml_str
