from api.bro_upload import object_upload


def test_gmn_startregistration_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_StartRegistration",
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


def test_gmn_startregistration_xml_replace():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_StartRegistration",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "broId": "GMN123",
            "correctionReason": "eigenCorrectie",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml


def test_gmn_startregistration_xml_move():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_StartRegistration",
        request_type="move",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "broId": "GMN123",
            "deliveryAccountableParty": "test",
            "correctionReason": "eigenCorrectie",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "moveRequest" in xml


def test_gmn_monitoringpoint_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_MeasuringPoint",
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


def test_gmn_monitoringpoint_xml_replace():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_MeasuringPoint",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "broId": "GMN123",
            "correctionReason": "eigenCorrectie",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml


def test_gmn_monitoringpoint_xml_move():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_MeasuringPoint",
        request_type="move",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "broId": "GMN123",
            "deliveryAccountableParty": "test",
            "correctionReason": "eigenCorrectie",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "moveRequest" in xml


def test_gmn_monitoringpointenddate_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_MeasuringPointEndDate",
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


def test_gmn_monitoringpointenddate_xml_replace():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_MeasuringPointEndDate",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "broId": "GMN123",
            "correctionReason": "eigenCorrectie",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml


def test_gmn_monitoringpointenddate_xml_move():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_MeasuringPointEndDate",
        request_type="move",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "broId": "GMN123",
            "deliveryAccountableParty": "test",
            "correctionReason": "eigenCorrectie",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "moveRequest" in xml


def test_gmn_tubereference_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_TubeReference",
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


def test_gmn_tubereference_xml_replace():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_TubeReference",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "broId": "GMN123",
            "correctionReason": "eigenCorrectie",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml


def test_gmn_tubereference_xml_move():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_TubeReference",
        request_type="move",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "broId": "GMN123",
            "deliveryAccountableParty": "test",
            "correctionReason": "eigenCorrectie",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "moveRequest" in xml


def test_gmn_closure_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_Closure",
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


def test_gmn_closure_xml_delete():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_Closure",
        request_type="delete",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "broId": "GMN123",
            "correctionReason": "eigenCorrectie",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "deleteRequest" in xml


def test_gmn_closure_xml_move():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_Closure",
        request_type="move",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "broId": "GMN123",
            "deliveryAccountableParty": "test",
            "correctionReason": "eigenCorrectie",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "moveRequest" in xml
