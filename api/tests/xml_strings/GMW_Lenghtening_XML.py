gmw_lengthening_xml = """<ns:registrationRequest xmlns:ns="http://www.broservices.nl/xsd/isgmw/1.1"
    xmlns:ns1="http://www.broservices.nl/xsd/brocommon/3.0"
    xmlns:ns2="http://www.broservices.nl/xsd/gmwcommon/1.1"
    xmlns:ns3="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <ns1:requestReference>GMW000000050650_Lengthening_1</ns1:requestReference>
    <ns1:deliveryAccountableParty>27376655</ns1:deliveryAccountableParty>
    <ns1:broId>GMW000000050650</ns1:broId>
    <ns1:qualityRegime>IMBRO/A</ns1:qualityRegime>

    <ns1:underPrivilege>ja</ns1:underPrivilege>

    <ns:sourceDocument>
        <ns:GMW_Lengthening>
            <ns:eventDate>
                <ns1:date>1986-09-12</ns1:date>
            </ns:eventDate>

            <ns:numberOfTubesLengthened>1</ns:numberOfTubesLengthened>

            <ns:monitoringTube>
                <ns:tubeNumber>2</ns:tubeNumber>
                <ns:variableDiameter>nee</ns:variableDiameter>
                <ns:tubeTopPosition uom="m">1.700</ns:tubeTopPosition>
                <ns:tubeTopPositioningMethod codeSpace="urn:bro:gmw:TubeTopPositioningMethod">onbekend</ns:tubeTopPositioningMethod>
                <ns:tubeMaterial codeSpace="urn:bro:gmw:TubeMaterial">pvc</ns:tubeMaterial>
                <ns:glue codeSpace="urn:bro:gmw:Glue">onbekend</ns:glue>
                <ns:plainTubePartLength uom="m">19.510</ns:plainTubePartLength>
            </ns:monitoringTube>

        </ns:GMW_Lengthening>
    </ns:sourceDocument>
</ns:registrationRequest>
"""
