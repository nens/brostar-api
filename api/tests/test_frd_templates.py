from api.bro_upload import object_upload


def test_frd_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="FRD_StartRegistration",
        request_type="registration",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={
            "objectIdAccountableParty": "party_3",
            "gmwBroId": "bro_id_456",
            "tubeNumber": "tube_123",
        },
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "registrationRequest" in xml


def test_frd_xml_replace():
    generator = object_upload.XMLGenerator(
        registration_type="FRD_StartRegistration",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={
            "objectIdAccountableParty": "party_3",
            "gmwBroId": "bro_id_456",
            "tubeNumber": "tube_123",
        },
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml


def test_frd_gem_measurement_xml_registration():
    generator = object_upload.XMLGenerator(
        registration_type="FRD_GEM_Measurement",
        request_type="registration",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={
            "measurementDate": "2025-02-06",
            "measurementOperatorKvk": "Kvk_789",
            "determinationProcedure": "Procedure_1",
            "evaluationProcedure": "Evaluation_1",
            "measurements": [{"value": 15, "unit": "ohm", "configuration": "config_1"}],
        },
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "registrationRequest" in xml


def test_frd_gem_measurement_xml_replace():
    generator = object_upload.XMLGenerator(
        registration_type="FRD_GEM_Measurement",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "test",
        },
        sourcedocs_data={
            "measurementDate": "2025-02-06",
            "measurementOperatorKvk": "Kvk_789",
            "determinationProcedure": "Procedure_1",
            "evaluationProcedure": "Evaluation_1",
            "measurements": [{"value": 15, "unit": "ohm", "configuration": "config_1"}],
        },
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml
