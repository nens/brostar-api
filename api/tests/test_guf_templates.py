from api.bro_upload import object_upload
from api.bro_upload.upload_datamodels import GUFStartRegistration


def test_guf_startregistration_xml():
    source_doc_dict = {
        "GUF_StartRegistration": {
            "objectIdAccountableParty": "Test1234",
            "deliveryContext": "waterwet",
            "startTime": "2023-03-20",
            "identificationLicence": "Test-1234",
            "legalType": "melding",
            "primaryUsageType": "bemaling",
            "secondaryUsageTypes": [],
            "humanConsumption": "nee",
            "licensedQuantities": [
                {
                    "licensedInOut": "onttrekken",
                    "maximumPerHour": 75,
                    "maximumPerDay": 1800,
                    "maximumPerMonth": 1800,
                    "maximumPerQuarter": 90000,
                    "maximumPerYear": 90000,
                },
                {
                    "licensedInOut": "inbrengen",
                    "maximumPerHour": 0,
                    "maximumPerDay": 0,
                    "maximumPerMonth": 0,
                    "maximumPerYear": 0,
                },
            ],
            "designInstallations": [
                {
                    "designInstallationId": "590241",
                    "installationFunction": "onttrekking",
                    "designInstallationPos": "214928 490230",
                    "licensedQuantities": [],
                    "energyCharacteristics": {
                        "energyCold": 0,
                        "energyWarm": 0,
                        "maximumInfiltrationTemperatureWarm": 25.0,
                        "averageInfiltrationTemperatureCold": 8.0,
                        "averageInfiltrationTemperatureWarm": 15.0,
                        "powerCold": 0,
                        "powerWarm": 0,
                        "averageColdWater": 240000,
                        "averageWarmWater": 240000,
                        "maximumYearQuantityCold": 360000,
                        "maximumYearQuantityWarm": 360000,
                    },
                    "designLoops": [],
                    "designSurfaceInfiltrations": [],
                    "designWells": [
                        {
                            "designWellId": "538269",
                            "wellFunctions": ["onttrekking"],
                            "height": 0,
                            "wellPos": "214928 490230",
                            "maximumWellDepth": 0,
                            "maximumWellCapacity": 75,
                            "designScreen": None,
                        }
                    ],
                }
            ],
        }
    }
    source_docs_data = GUFStartRegistration(**source_doc_dict["GUF_StartRegistration"])
    assert len(source_docs_data.design_installations[0].licensed_quantities) == 0
    assert source_docs_data.licensed_quantities[0].maximum_per_hour == 75
    print(source_docs_data.model_dump(mode="json", by_alias=True))
    generator = object_upload.XMLGenerator(
        registration_type="GUF_StartRegistration",
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
    assert "GUF_StartRegistration" in xml
    assert "identificationLicence" in xml
    assert "designInstallationId" in xml
    assert "designWellId" in xml
