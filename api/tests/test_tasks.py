import uuid
from unittest import mock

from api.tasks import (
    check_delivery_status_task,
    deliver_xml_file_task,
    generate_xml_file_task,
    validate_xml_file_task,
)


@mock.patch("api.tasks.api_models.UploadTask.objects.get")
@mock.patch("api.tasks.XMLGenerator")
def test_generate_xml_file_task(mock_generator_class, mock_get):
    uuid_string = f"_{uuid.uuid4()}"
    mock_instance = mock.Mock()
    mock_get.return_value = mock_instance

    mock_generator = mock.Mock()
    mock_generator.create_xml_file.return_value = "<xml>dummy</xml>"
    mock_generator_class.return_value = mock_generator

    result = generate_xml_file_task(uuid_string)

    assert result["upload_task_instance_uuid"] == uuid_string
    assert result["xml_file"] == "<xml>dummy</xml>"
    mock_instance.save.assert_called_once()


@mock.patch("api.tasks.api_models.UploadTask.objects.get")
@mock.patch("api.tasks.utils.validate_xml_file")
def test_validate_xml_file_task_valid(mock_validate, mock_get):
    mock_instance = mock.Mock()
    mock_get.return_value = mock_instance

    context = {"upload_task_instance_uuid": "uuid", "xml_file": "<xml>dummy</xml>"}
    mock_validate.return_value = {"status": "VALIDE"}

    result = validate_xml_file_task(context, "user", "pass")

    assert result["bro_username"] == "user"
    assert mock_instance.save.called


@mock.patch("api.tasks.api_models.UploadTask.objects.get")
@mock.patch("api.tasks.utils.create_upload_url")
@mock.patch("api.tasks.utils.add_xml_to_upload")
@mock.patch("api.tasks.utils.create_delivery")
def test_deliver_xml_file_task(
    mock_create_delivery, mock_add_xml, mock_create_upload_url, mock_get
):
    mock_instance = mock.Mock()
    mock_get.return_value = mock_instance

    mock_create_upload_url.return_value = "upload_url"
    mock_create_delivery.return_value = "delivery_url"

    context = {
        "upload_task_instance_uuid": "uuid",
        "xml_file": "<xml>",
        "bro_username": "user",
        "bro_password": "pass",
    }
    result = deliver_xml_file_task(context)

    assert result["delivery_url"] == "delivery_url"
    assert mock_instance.save.called


@mock.patch("api.tasks.api_models.UploadTask.objects.get")
@mock.patch("api.tasks.utils.check_delivery_status")
def test_check_delivery_status_task_delivered(mock_check_status, mock_get):
    mock_instance = mock.Mock()
    mock_get.return_value = mock_instance

    mock_check_status.return_value = {
        "status": "DOORGELEVERD",
        "brondocuments": [
            {"status": "OPGENOMEN_LVBRO", "broId": "GMW00000083478", "errors": []}
        ],
    }

    context = {
        "upload_task_instance_uuid": "uuid",
        "delivery_url": "url",
        "bro_username": "u",
        "bro_password": "p",
    }
    check_delivery_status_task(context)

    assert mock_instance.status == "COMPLETED"
    assert mock_instance.bro_id == "GMW00000083478"
    assert mock_instance.save.called
