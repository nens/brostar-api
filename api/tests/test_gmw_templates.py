from api.bro_upload import object_upload


def test_gmw_construction_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="GMW_Construction",
        request_type="registration",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "registrationRequest" in xml


def test_gmw_construction_xml_replace():
    generator = object_upload.XMLGenerator(
        registration_type="GMW_Construction",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "correctionReason": "eigenCorrectie",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml


def test_gmw_construction_xml_move():
    generator = object_upload.XMLGenerator(
        registration_type="GMW_Construction",
        request_type="move",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
            "correctionReason": "eigenCorrectie",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "moveRequest" in xml


def test_gmw_groundlevelmeasuring_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="GMW_GroundLevelMeasuring",
        request_type="registration",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "registrationRequest" in xml


def test_gmw_groundlevelmeasuring_xml_replace():
    generator = object_upload.XMLGenerator(
        registration_type="GMW_GroundLevelMeasuring",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "correctionReason": "eigenCorrectie",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml


def test_gmw_groundlevelmeasuring_xml_move():
    generator = object_upload.XMLGenerator(
        registration_type="GMW_GroundLevelMeasuring",
        request_type="move",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
            "correctionReason": "eigenCorrectie",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "moveRequest" in xml


def test_gmw_groundlevel_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="GMW_GroundLevel",
        request_type="registration",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "registrationRequest" in xml


def test_gmw_groundlevel_xml_replace():
    generator = object_upload.XMLGenerator(
        registration_type="GMW_GroundLevel",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "correctionReason": "eigenCorrectie",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml


def test_gmw_groundlevel_xml_move():
    generator = object_upload.XMLGenerator(
        registration_type="GMW_GroundLevel",
        request_type="move",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
            "correctionReason": "eigenCorrectie",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "moveRequest" in xml
