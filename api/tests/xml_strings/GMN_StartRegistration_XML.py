gmn_startregistration_xml = """<registrationRequest xmlns="http://www.broservices.nl/xsd/isgmn/1.0"
    xmlns:brocom="http://www.broservices.nl/xsd/brocommon/3.0"
    xmlns:gml="http://www.opengis.net/gml/3.2"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.broservices.nl/xsd/isgmn/1.0 https://schema.broservices.nl/xsd/isgmn/1.0/isgmn-messages.xsd">
    <brocom:requestReference>test</brocom:requestReference>
    <brocom:deliveryAccountableParty>27376655</brocom:deliveryAccountableParty>
    <brocom:qualityRegime>IMBRO/A</brocom:qualityRegime>
    <sourceDocument>
        <GMN_StartRegistration gml:id="id_0001">
            <objectIdAccountableParty>test</objectIdAccountableParty>
            <name>test</name>
            <deliveryContext codeSpace="urn:bro:gmn:DeliveryContext">kaderrichtlijnWater</deliveryContext>
            <monitoringPurpose codeSpace="urn:bro:gmn:MonitoringPurpose">strategischBeheerKwaliteitRegionaal</monitoringPurpose>
            <groundwaterAspect codeSpace="urn:bro:gmn:GroundwaterAspect">kwantiteit</groundwaterAspect>
            <startDateMonitoring>
                <brocom:date>2024-01-01</brocom:date>
            </startDateMonitoring>

            <measuringPoint>
                <MeasuringPoint gml:id="measuringpoint_1">
                    <measuringPointCode>GMW000000038946</measuringPointCode>
                    <monitoringTube>
                        <GroundwaterMonitoringTube gml:id="tube_1">
                            <broId>GMW000000038946</broId>
                            <tubeNumber>1</tubeNumber>
                        </GroundwaterMonitoringTube>
                    </monitoringTube>
                </MeasuringPoint>
            </measuringPoint>

            <measuringPoint>
                <MeasuringPoint gml:id="measuringpoint_2">
                    <measuringPointCode>GMW000000038946</measuringPointCode>
                    <monitoringTube>
                        <GroundwaterMonitoringTube gml:id="tube_2">
                            <broId>GMW000000038946</broId>
                            <tubeNumber>2</tubeNumber>
                        </GroundwaterMonitoringTube>
                    </monitoringTube>
                </MeasuringPoint>
            </measuringPoint>

        </GMN_StartRegistration>
    </sourceDocument>
</registrationRequest>
"""
