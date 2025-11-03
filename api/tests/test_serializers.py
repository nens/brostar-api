from unittest.mock import Mock

import pytest
from rest_framework.exceptions import ValidationError

from api import models as api_models
from api import serializers as api_serializers
from api.tests import fixtures

# this setup is chosen because ruff removes the fixture imports in other methods
organisation = fixtures.organisation


@pytest.mark.django_db
def test_organisation_serialization(organisation):
    serializer = api_serializers.OrganisationSerializer(instance=organisation)
    assert serializer.data["name"] == organisation.name


@pytest.mark.django_db
def test_organisation_deserialization(organisation):
    input_data = {"name": "Test Org", "kvk_number": "12345678"}
    serializer = api_serializers.OrganisationSerializer(data=input_data)
    assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
def test_valid_data_importtask_serialization(organisation):
    data = {
        "data_owner": organisation.uuid,
        "kvk_number": organisation.kvk_number,
        "bro_domain": "GMN",
        "status": "PENDING",
    }
    serializer = api_serializers.ImportTaskSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    serialized_data = serializer.data
    assert serialized_data["bro_domain"] == "GMN"


@pytest.mark.django_db
def test_valid_data_importtask_deserialization(organisation):
    data = {
        "data_owner": organisation,
        "kvk_number": organisation.kvk_number,
        "bro_domain": "GMN",
        "status": "PENDING",
    }
    upload_task = api_models.ImportTask.objects.create(**data)
    serializer = api_serializers.ImportTaskSerializer(instance=upload_task)
    serialized_data = serializer.data
    assert serialized_data["bro_domain"] == "GMN"


@pytest.mark.django_db
def test_invalid_data_importtask_validation(organisation):
    data = {
        "data_owner": organisation,
        "kvk_number": organisation.kvk_number,
        "bro_domain": "Non-existing-domain",
        "status": "PENDING",
    }
    serializer = api_serializers.ImportTaskSerializer(data=data)
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_valid_data_uploadtask_serialization(organisation):
    data = {
        "data_owner": organisation.uuid,
        "bro_domain": "GMN",
        "project_number": "1",
        "registration_type": "GMN_StartRegistration",
        "request_type": "registration",
        "status": "PENDING",
        "metadata": {},
        "sourcedocument_data": {},
    }
    serializer = api_serializers.UploadTaskSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    serialized_data = serializer.data
    assert serialized_data["bro_domain"] == "GMN"


@pytest.mark.django_db
def test_valid_data_uploadtask_deserialization(organisation):
    data = {
        "data_owner": organisation,
        "bro_domain": "GMN",
        "project_number": "1",
        "registration_type": "GMN_StartRegistration",
        "request_type": "registration",
        "status": "PENDING",
        "metadata": {},
        "sourcedocument_data": {},
    }
    upload_task = api_models.UploadTask.objects.create(**data)
    serializer = api_serializers.UploadTaskSerializer(instance=upload_task)
    serialized_data = serializer.data
    assert serialized_data["bro_domain"] == "GMN"


@pytest.mark.django_db
def test_invalid_data_uploadtask_validation(organisation):
    data = {
        "data_owner": organisation,
        "bro_domain": "Non-existing-domain",
        "project_number": "1",
        "registration_type": "GMN_StartRegistration",
        "request_type": "registration",
        "status": "PENDING",
        "metadata": {},
        "sourcedocument_data": {},
    }
    serializer = api_serializers.UploadTaskSerializer(data=data)
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)


### Test serializer adjustments for UploadTaskSerializer
@pytest.mark.django_db
def test_valid_data_uploadtask_gar_serialization(organisation):
    data = {
        "data_owner": organisation.uuid,
        "bro_domain": "GAR",
        "project_number": "1",
        "registration_type": "GAR",
        "request_type": "registration",
        "status": "PENDING",
        "metadata": {
            "deliveryAccountableParty": "51468751",
            "qualityRegime": "IMBRO",
            "requestReference": "GAR: 2021-05-18T10:25:52Z-None (2025-10-21T17:25:22Z)",
        },
        "sourcedocument_data": {
            "fieldResearch": {
                "abnormalFilter": "onbekend",
                "abnormalityInCooling": "onbekend",
                "abnormalityInDevice": "onbekend",
                "colourStrength": None,
                "fieldMeasurements": [
                    {
                        "fieldMeasurementValue": 348.0,
                        "parameter": 3548,
                        "qualityControlStatus": "onbekend",
                        "unit": "mS/m",
                    },
                    {
                        "fieldMeasurementValue": 5.71,
                        "parameter": 1398,
                        "qualityControlStatus": "onbekend",
                        "unit": "1",
                    },
                ],
                "filterAerated": "onbekend",
                "groundWaterLevelDroppedTooMuch": "onbekend",
                "hoseReused": "onbekend",
                "pollutedByEngine": "onbekend",
                "primaryColour": None,
                "pumpType": "onbekend",
                "sampleAerated": "onbekend",
                "samplingDateTime": "2021-06-22T00:00:00+01:00",
                "samplingOperator": "51468751",
                "samplingStandard": "onbekend",
                "secondaryColour": None,
                "temperatureDifficultToMeasure": "onbekend",
            },
            "gmwBroId": "GMW000000082110",
            "groundwaterMonitoringNets": ["GMN000000002554"],
            "laboratoryAnalyses": [
                {
                    "analysisProcesses": [
                        {
                            "analyses": [
                                {
                                    "analysisMeasurementValue": 4387.0,
                                    "limitSymbol": None,
                                    "parameter": 3548,
                                    "qualityControlStatus": "onbekend",
                                    "reportingLimit": None,
                                    "unit": "mS/cm",
                                },
                                {
                                    "analysisMeasurementValue": 635.0,
                                    "limitSymbol": None,
                                    "parameter": 1398,
                                    "qualityControlStatus": "onbekend",
                                    "reportingLimit": None,
                                    "unit": "1",
                                },
                                {
                                    "analysisMeasurementValue": 198.0,
                                    "limitSymbol": None,
                                    "parameter": 1522,
                                    "qualityControlStatus": "onbekend",
                                    "reportingLimit": None,
                                    "unit": "Cel",
                                },
                                {
                                    "analysisMeasurementValue": 8285.0,
                                    "limitSymbol": None,
                                    "parameter": 1318,
                                    "qualityControlStatus": "onbekend",
                                    "reportingLimit": None,
                                    "unit": "mg/l",
                                },
                            ],
                            "analyticalTechnique": "AAS",
                            "date": "2021-06-22",
                            "valuationMethod": "CIW",
                        }
                    ],
                    "responsibleLaboratoryKvk": "51468751",
                }
            ],
            "objectIdAccountableParty": "B46B0092_2",
            "qualityControlMethod": "qCProtocolProvinciesEnRIVMv2021",
            "tubeNumber": "2",
        },
    }
    serializer = api_serializers.UploadTaskSerializer(data=data)
    assert serializer.is_valid(), serializer.errors

    instance = serializer.save()
    serializer = api_serializers.UploadTaskSerializer(
        instance, context={"view": Mock(action="list")}
    )
    serialized_data = serializer.data

    assert serialized_data["bro_domain"] == "GAR"
    assert (
        serialized_data["sourcedocument_data"]["fieldResearch"][
            "fieldMeasurementsCount"
        ]
        == 2
    )
    assert (
        serialized_data["sourcedocument_data"]["laboratoryAnalyses"][0][
            "analysisProcesses"
        ][0]["analysesCount"]
        == 4
    )
    assert serialized_data["sourcedocument_data"]["laboratoryAnalysesCount"] == 1


@pytest.mark.django_db
def test_valid_data_uploadtask_gld_serialization(organisation):
    data = {
        "data_owner": organisation.uuid,
        "bro_domain": "GLD",
        "project_number": "1",
        "registration_type": "GLD_Addition",
        "request_type": "registration",
        "status": "PENDING",
        "metadata": {
            "broId": "GLD000000063772",
            "correctionReason": None,
            "deliveryAccountableParty": "51468751",
            "qualityRegime": "IMBRO",
            "requestReference": "GLD000000063772: IMBRO controlemeting 2021-05-18T10:25:52Z-None (2025-10-21T17:25:22Z)",
        },
        "sourcedocument_data": {
            "airPressureCompensationType": None,
            "beginPosition": "2021-11-30",
            "date": "2023-08-21",
            "endPosition": "2023-08-21",
            "evaluationProcedure": "vitensBeoordelingsprotocolGrondwater",
            "investigatorKvk": "51468751",
            "measurementInstrumentType": "elektronischPeilklokje",
            "measurementTimeseriesId": "_d9169939-e069-4690-88f0-86e779d7b895",
            "observationId": "_4e84ea51-f340-43d3-bb4b-1f9cfa68c303",
            "observationProcessId": "_447266fd-b815-4eeb-bce8-65ad8119f33c",
            "observationType": "controlemeting",
            "processReference": "vitensMeetprotocolGrondwater",
            "resultTime": "2023-08-21T09:53:31+02:00",
            "timeValuePairs": [
                {
                    "censorReason": None,
                    "censoringLimitvalue": None,
                    "statusQualityControl": "goedgekeurd",
                    "time": "2021-11-30T11:04:27+01:00",
                    "value": 10.32,
                },
                {
                    "censorReason": None,
                    "censoringLimitvalue": None,
                    "statusQualityControl": "goedgekeurd",
                    "time": "2022-06-10T11:54:38+02:00",
                    "value": 10.28,
                },
                {
                    "censorReason": None,
                    "censoringLimitvalue": None,
                    "statusQualityControl": "goedgekeurd",
                    "time": "2022-11-24T11:00:12+01:00",
                    "value": 10.08,
                },
                {
                    "censorReason": None,
                    "censoringLimitvalue": None,
                    "statusQualityControl": "goedgekeurd",
                    "time": "2023-02-16T12:05:53+01:00",
                    "value": 10.35,
                },
                {
                    "censorReason": None,
                    "censoringLimitvalue": None,
                    "statusQualityControl": "goedgekeurd",
                    "time": "2023-02-16T12:36:39+01:00",
                    "value": 10.33,
                },
                {
                    "censorReason": None,
                    "censoringLimitvalue": None,
                    "statusQualityControl": "goedgekeurd",
                    "time": "2023-05-22T09:40:33+02:00",
                    "value": 10.33,
                },
                {
                    "censorReason": None,
                    "censoringLimitvalue": None,
                    "statusQualityControl": "goedgekeurd",
                    "time": "2023-08-21T09:53:31+02:00",
                    "value": 10.29,
                },
            ],
            "validationStatus": None,
        },
    }
    serializer = api_serializers.UploadTaskSerializer(data=data)
    assert serializer.is_valid(), serializer.errors

    instance = serializer.save()
    serializer = api_serializers.UploadTaskSerializer(
        instance, context={"view": Mock(action="list")}
    )
    serialized_data = serializer.data

    assert serialized_data["bro_domain"] == "GLD"
    assert serialized_data["sourcedocument_data"]["timeValuePairsCount"] == 7
