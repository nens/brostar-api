import pytest
from rest_framework.exceptions import ValidationError
from api import serializers as api_serializers
from api import models as api_models
from api.tests.fixtures import organisation, gmn, gmw

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
        "metadata":{},
        "sourcedocument_data":{},
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
        "metadata":{},
        "sourcedocument_data":{},
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
        "metadata":{},
        "sourcedocument_data":{},
    }
    serializer = api_serializers.UploadTaskSerializer(data=data)
    with pytest.raises(ValidationError):
        serializer.is_valid(raise_exception=True)