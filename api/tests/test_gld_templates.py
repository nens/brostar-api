from api.bro_upload import object_upload


def test_gld_startregistration_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="GLD_StartRegistration",
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


def test_gld_startregistration_xml_replace():
    generator = object_upload.XMLGenerator(
        registration_type="GLD_StartRegistration",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={},
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml


def test_gld_addition_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="GLD_Addition",
        request_type="registration",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={
            "observationId": "_12345",
            "investigatorKvk": "Kvk_123",
            "observationType": "controlemeting",
            "measurementInstrumentType": "type_1",
            "timeValuePairs": [
                {
                    "time": "2025-02-06T10:00:00",
                    "value": 12.5,
                    "statusQualityControl": "onbekend",
                }
            ],
        },
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "registrationRequest" in xml


def test_gld_addition_xml_replace():
    generator = object_upload.XMLGenerator(
        registration_type="GLD_Addition",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={
            "observationId": "_12345",
            "investigatorKvk": "Kvk_123",
            "observationType": "controlemeting",
            "measurementInstrumentType": "type_1",
            "timeValuePairs": [
                {
                    "time": "2025-02-06T10:00:00",
                    "value": 12.5,
                    "statusQualityControl": "onbekend",
                }
            ],
        },
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml


def test_gld_addition_xml_delete():
    generator = object_upload.XMLGenerator(
        registration_type="GLD_Addition",
        request_type="delete",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={
            "observationId": "_12345",
            "investigatorKvk": "Kvk_123",
            "observationType": "controlemeting",
            "measurementInstrumentType": "type_1",
            "timeValuePairs": [
                {
                    "time": "2025-02-06T10:00:00",
                    "value": 12.5,
                    "statusQualityControl": "onbekend",
                }
            ],
        },
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "deleteRequest" in xml
