import logging
import time
from logging import getLogger

from celery import chain, shared_task

import api.models as api_models
from api.bro_import import bulk_import
from api.bro_upload import utils
from api.bro_upload.gar_bulk_upload import GARBulkUploader
from api.bro_upload.gld_bulk_upload import GLDBulkUploader
from api.bro_upload.gmn_bulk_upload import GMNBulkUploader
from api.bro_upload.object_upload import (
    BRODelivery,
    DeliveryError,
    XMLGenerator,
    XMLValidationError,
)

logger = logging.getLogger("general")


logger = getLogger(__name__)


@shared_task(queue="Upload")
def generate_xml_file_task(upload_task_instance_uuid: str):
    upload_task_instance = api_models.UploadTask.objects.get(
        uuid=upload_task_instance_uuid
    )

    try:
        generator = XMLGenerator(
            upload_task_instance.registration_type,
            upload_task_instance.request_type,
            upload_task_instance.metadata,
            upload_task_instance.sourcedocument_data,
        )
        xml = generator.create_xml_file()
        upload_task_instance.progress = 25
        upload_task_instance.save(update_fields=["progress"])

        return {
            "upload_task_instance_uuid": upload_task_instance_uuid,
            "xml_file": xml,
        }

    except Exception as e:
        logger.exception(e)
        raise RuntimeError(f"Error generating XML file: {e}") from e


@shared_task(queue="Upload")
def validate_xml_file_task(context: dict, bro_username: str, bro_password: str):
    upload_task_instance = api_models.UploadTask.objects.get(
        uuid=context["upload_task_instance_uuid"]
    )

    validation_response = utils.validate_xml_file(
        context["xml_file"],
        bro_username,
        bro_password,
        upload_task_instance.project_number,
    )

    context.update({"bro_password": bro_password, "bro_username": bro_username})

    if validation_response["status"] != "VALIDE":
        upload_task_instance.bro_errors = validation_response["errors"]
        upload_task_instance.save()
        raise XMLValidationError("Errors while validating the XML file")

    upload_task_instance.progress = 50.0
    upload_task_instance.save()
    return context


@shared_task(queue="Upload")
def deliver_xml_file_task(context):
    upload_task_instance = api_models.UploadTask.objects.get(
        uuid=context["upload_task_instance_uuid"]
    )
    bro_username = context["bro_username"]
    bro_password = context["bro_password"]

    upload_url = utils.create_upload_url(
        bro_username,
        bro_password,
        upload_task_instance.project_number,
    )
    utils.add_xml_to_upload(
        context["xml_file"],
        upload_url,
        bro_username,
        bro_password,
    )
    delivery_url = utils.create_delivery(
        upload_url,
        bro_username,
        bro_password,
        upload_task_instance.project_number,
    )
    upload_task_instance.bro_delivery_url = delivery_url
    upload_task_instance.progress = 75.0
    upload_task_instance.save()
    context["delivery_url"] = delivery_url
    return context


@shared_task(queue="Upload")
def check_delivery_status_task(context):
    delivery_status = "AANGELEVERD"
    retry_count = 0
    bro_id = None
    while delivery_status != "DOORGELEVERD" or retry_count > 4:
        delivery_info = utils.check_delivery_status(
            context["delivery_url"], context["bro_username"], context["bro_password"]
        )

        errors = delivery_info["brondocuments"][0]["errors"]

        if errors:
            raise DeliveryError(f"Errors found after delivering the XML file: {errors}")

        delivery_status = delivery_info["status"]
        delivery_brondocument_status = delivery_info["brondocuments"][0]["status"]

        if (
            delivery_status == "DOORGELEVERD"
            and delivery_brondocument_status == "OPGENOMEN_LVBRO"
        ):
            # Set BRO id to self to enable an import task based on the bro id. This keeps the data up2date in the api.
            bro_id = delivery_info["brondocuments"][0]["broId"]
        time.sleep(10)

    upload_task_instance = api_models.UploadTask.objects.get(
        uuid=context["upload_task_instance_uuid"]
    )
    upload_task_instance.bro_id = bro_id
    upload_task_instance.progress = 100.0 if bro_id else 95.0
    upload_task_instance.status = "COMPLETED" if bro_id else "UNFINISHED"
    upload_task_instance.log = (
        f"Upload geslaagd: {bro_id}"
        if bro_id
        else "After 4 times checking, the delivery status in the BRO was still not 'DOORGELEVERD'. Please checks its status manually."
    )
    upload_task_instance.save()


@shared_task(queue="default")
def import_bro_data_task(import_task_instance_uuid: str) -> None:
    """Celery task that imports the data based on a KvK and BRO Domain.

    It is called when a valid POST request is done on the importtask endpoint is done.
    The BulkImporter class is used to handle the whole proces.
    The status and logging of the process can be found in the ImportTask instance.
    """
    try:
        importer = bulk_import.BulkImporter(import_task_instance_uuid)
        importer.run()
    except Exception as e:
        logger.exception(e)


@shared_task(queue="Upload")
def upload_bro_data_task(
    upload_task_instance_uuid: str,
    bro_username: str,
    bro_password: str,
) -> None:
    """Celery task that uploads data to the BRO.

    It is called when a valid POST request is done on the uploadtask endpoint is done.
    The BRODelivery class is used to handle the whole proces of delivery.
    The status and logging of the process can be found in the UploadTask instance.
    """
    try:
        uploader = BRODelivery(upload_task_instance_uuid, bro_username, bro_password)
        uploader.process()
    except Exception as e:
        logger.exception(e)


def upload_task(
    upload_task_instance_uuid: str,
    bro_username: str,
    bro_password: str,
) -> None:
    """Celery chain that:

    1. Creates an XML
    2. Validates the XML to the BRO API
    3. Delivers the XML to the BRO

    It is called when a valid POST request is done on the uploadtask endpoint is done.
    The BRODelivery class is used to handle the whole proces of delivery.
    The status and logging of the process can be found in the UploadTask instance.
    """
    workflow = chain(
        generate_xml_file_task.s(upload_task_instance_uuid),
        validate_xml_file_task.s(bro_username, bro_password),
        deliver_xml_file_task.s(),
        check_delivery_status_task.s(),
    )
    workflow.apply_async()


@shared_task(queue="Upload")
def gar_bulk_upload_task(
    bulk_upload_instance_uuid: str,
    fieldwork_upload_file_uuid: str,
    lab_upload_file_uuid: str,
) -> None:
    """Celery task that handles the bulk upload for GAR data after a POST on the bulkupload endpoint."""
    try:
        uploader = GARBulkUploader(
            bulk_upload_instance_uuid,
            fieldwork_upload_file_uuid,
            lab_upload_file_uuid,
        )
        uploader.process()
    except Exception as e:
        logger.exception(e)


@shared_task(queue="Upload")
def gld_bulk_upload_task(
    bulk_upload_instance_uuid: str,
    measurement_tvp_file_uuid: str,
) -> None:
    """Celery task that handles the bulk upload for GAR data after a POST on the bulkupload endpoint."""
    try:
        uploader = GLDBulkUploader(
            bulk_upload_instance_uuid,
            measurement_tvp_file_uuid,
        )
        uploader.process()
    except Exception as e:
        logger.exception(e)


@shared_task(queue="Upload")
def gmn_bulk_upload_task(
    bulk_upload_instance_uuid: str,
    file_uuid: str,
) -> None:
    """Celery task that handles the bulk upload for GAR data after a POST on the bulkupload endpoint."""
    try:
        uploader = GMNBulkUploader(
            bulk_upload_instance_uuid,
            file_uuid,
        )
        uploader.process()
    except Exception as e:
        logger.exception(e)
