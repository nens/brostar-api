from api.bro_upload import object_upload, utils


def test_xml_generator1():
    generator = object_upload.XMLGenerator(
        registration_type="GMN_StartRegistration",
        request_type="registration",
        metadata={
            "requestReference": "test",
            "deliveryAccountableParty": "27376655",
            "qualityRegime": "IMBRO/A",
        },
        sourcedocs_data={
            "objectIdAccountableParty": "test",
            "name": "test",
            "deliveryContext": "kaderrichtlijnWater",
            "monitoringPurpose": "strategischBeheerKwaliteitRegionaal",
            "groundwaterAspect": "kwantiteit",
            "startDateMonitoring": "2024-01-01",
            "measuringPoints": [
                {
                    "measuringPointCode": "GMW000000038946",
                    "broId": "GMW000000038946",
                    "tubeNumber": "1",
                },
                {
                    "measuringPointCode": "GMW000000038946",
                    "broId": "GMW000000038946",
                    "tubeNumber": "2",
                },
            ],
        },
    )

    assert generator.create_xml_file()
    assert generator.status == "COMPLETED"


def test_xml_generator2():
    """Tests a non existing combination of registration_type and request type."""
    generator = object_upload.XMLGenerator(
        registration_type="GMN_StartRegistration",
        request_type="insert",
        metadata={},
        sourcedocs_data={},
    )
    generator.create_xml_file()

    assert generator.status == "FAILED"
    assert "does not exist" in generator.error_message


def test_xml_generator3():
    generator = object_upload.XMLGenerator(
        registration_type="GMW_Lengthening",
        request_type="registration",
        metadata={
            "requestReference": "GMW000000050650_Lengthening_1",
            "deliveryAccountableParty": "27376655",
            "broId": "GMW000000050650",
            "qualityRegime": "IMBRO/A",
            "underPrivilege": "ja",
        },
        sourcedocs_data={
            "eventDate": "1986-09-12",
            "monitoringTubes": [
                {
                    "tubeNumber": 2,
                    "variableDiameter": "nee",
                    "tubeTopPosition": "1.700",
                    "tubeTopPositioningMethod": "onbekend",
                    "tubeMaterial": "pvc",
                    "glue": "onbekend",
                    "plainTubePartLength": "19.510",
                }
            ],
        },
    )

    assert generator.create_xml_file()
    assert generator.status == "COMPLETED"


def test_simplify_validation_errors():
    input_data = [
        {
            "type": "missing",
            "loc": ["requestReference"],
            "msg": "Field required",
            "input": {},
            "url": "https://errors.pydantic.dev/2.7/v/missing",
        },
        {
            "type": "missing",
            "loc": ["deliveryAccountableParty"],
            "msg": "Field required",
            "input": {},
            "url": "https://errors.pydantic.dev/2.7/v/missing",
        },
        {
            "type": "missing",
            "loc": ["qualityRegime"],
            "msg": "Field required",
            "input": {},
            "url": "https://errors.pydantic.dev/2.7/v/missing",
        },
    ]
    expected_output = {
        "requestReference": "Field required",
        "deliveryAccountableParty": "Field required",
        "qualityRegime": "Field required",
    }

    output = utils.simplify_validation_errors(input_data)

    assert output == expected_output
