from api.bro_upload import object_upload
from api.bro_upload.upload_datamodels import (
    GPDAddReport,
    GPDEndRegistration,
    GPDStartRegistration,
)


def test_gpd_startregistration_xml():
    source_doc_dict = {
        "objectIdAccountableParty": "Test1234",
    }
    source_docs_data = GPDStartRegistration(**source_doc_dict)
    generator = object_upload.XMLGenerator(
        registration_type="GPD_StartRegistration",
        request_type="registration",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "12345678",
        },
        sourcedocs_data=source_docs_data.model_dump(mode="json", by_alias=True),
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "registrationRequest" in xml
    assert "GPD_StartRegistration" in xml
    assert "Test1234" in xml
    assert "publiclyAvailable" not in xml

    source_doc_dict = {
        "objectIdAccountableParty": "Test1234",
        "publiclyAvailable": "ja",
    }
    source_docs_data = GPDStartRegistration(**source_doc_dict)
    generator = object_upload.XMLGenerator(
        registration_type="GPD_StartRegistration",
        request_type="registration",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "12345678",
        },
        sourcedocs_data=source_docs_data.model_dump(mode="json", by_alias=True),
    )
    xml = generator.create_xml_file()
    assert xml is not None
    assert "registrationRequest" in xml
    assert "GPD_StartRegistration" in xml
    assert "Test1234" in xml
    assert "publiclyAvailable" in xml


def test_gpd_addreport_xml():
    source_doc_dict = {
        "reportId": "Report1234",
        "method": "berekening",
        "volumeSeries": [
            {
                "waterInOut": "onttrokken",
                "volume": 1000,
                "temperature": "koud",
                "beginDate": "2024-01-01",
                "endDate": "2024-01-31",
            }
        ],
        "groundwaterUsageFacilityBroId": "GUF1234",
    }
    source_docs_data = GPDAddReport(**source_doc_dict)
    generator = object_upload.XMLGenerator(
        registration_type="GPD_AddReport",
        request_type="replace",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "12345678",
            "correctionReason": "eigenCorrectie",
        },
        sourcedocs_data=source_docs_data.model_dump(mode="json", by_alias=True),
    )
    xml = generator.create_xml_file()
    assert xml is not None
    assert "replaceRequest" in xml
    assert "GPD_AddReport" in xml
    assert "Report1234" in xml
    assert (
        '<gpdcom:method codeSpace="urn:bro:gpd:Method">berekening</gpdcom:method>'
        in xml
    )
    assert "GUF1234" in xml


def test_gpd_endregistration_xml():
    source_doc_dict = {
        "objectIdAccountableParty": "Test1234",
    }
    source_docs_data = GPDEndRegistration(**source_doc_dict)
    generator = object_upload.XMLGenerator(
        registration_type="GPD_EndRegistration",
        request_type="registration",
        metadata={
            "requestReference": "test",
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "12345678",
        },
        sourcedocs_data=source_docs_data.model_dump(mode="json", by_alias=True),
    )

    xml = generator.create_xml_file()
    assert xml is not None
    assert "registrationRequest" in xml
    assert "GPD_EndRegistration" in xml
    assert "Test1234" not in xml
