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
    DeliveryError,
    XMLGenerator,
    XMLValidationError,
)

logger = logging.getLogger("general")


logger = getLogger(__name__)


@shared_task(queue="upload")
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
        upload_task_instance.log = "XML generated."
        upload_task_instance.save(update_fields=["progress", "log"])

        return {
            "upload_task_instance_uuid": upload_task_instance_uuid,
            "xml_file": xml,
        }

    except Exception as e:
        logger.exception(RuntimeError(f"Error generating XML file: {e}"))
        return


@shared_task(queue="upload")
def validate_xml_file_task(context: dict, bro_username: str, bro_password: str):
    if context is None:
        return None

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
        upload_task_instance.progress = 50.0
        upload_task_instance.log = "XML is not valid"
        upload_task_instance.bro_errors = validation_response["errors"]
        upload_task_instance.save()
        logger.exception(XMLValidationError("Errors while validating the XML file"))
        return

    upload_task_instance.progress = 50.0
    upload_task_instance.log = "XML is valid"
    upload_task_instance.save(update_fields=["progress", "log"])
    return context


@shared_task(queue="upload")
def deliver_xml_file_task(context):
    if context is None:
        return None

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
    upload_task_instance.log = "XML delivered."
    upload_task_instance.save()
    context["delivery_url"] = delivery_url
    return context


@shared_task(queue="upload")
def check_delivery_status_task(context):
    if context is None:
        return None

    upload_task_instance = api_models.UploadTask.objects.get(
        uuid=context["upload_task_instance_uuid"]
    )
    delivery_status = "AANGELEVERD"
    retry_count = 0
    bro_id = None
    while delivery_status != "DOORGELEVERD" or retry_count > 4:
        delivery_info = utils.check_delivery_status(
            context["delivery_url"], context["bro_username"], context["bro_password"]
        )

        errors = delivery_info["brondocuments"][0]["errors"]

        if errors:
            logger.exception(
                DeliveryError(f"Errors found after delivering the XML file: {errors}")
            )
            upload_task_instance.progress = 80
            upload_task_instance.status = "FAILED"
            upload_task_instance.log = (
                f"Errors found after delivering the XML file: {errors}"
            )
            upload_task_instance.save()
            return

        delivery_status = delivery_info["status"]
        delivery_brondocument_status = delivery_info["brondocuments"][0]["status"]

        if (
            delivery_status == "DOORGELEVERD"
            and delivery_brondocument_status == "OPGENOMEN_LVBRO"
        ):
            # Set BRO id to self to enable an import task based on the bro id. This keeps the data up2date in the api.
            bro_id = delivery_info["brondocuments"][0]["broId"]
        time.sleep(10)

    upload_task_instance.bro_id = bro_id
    upload_task_instance.progress = 100.0 if bro_id else 95.0
    upload_task_instance.status = "COMPLETED" if bro_id else "UNFINISHED"
    upload_task_instance.log = (
        f"Upload geslaagd: {bro_id}"
        if bro_id
        else "Na 4 keer (40s) een controle te hebben gedaan was de status in de BRO nog niet 'DOORGELEVERD'. Kijk handmatig."
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


@shared_task(queue="upload")
def handle_task_error(request, exc, traceback, upload_task_instance_uuid, step_name):
    """Handle task errors by updating the UploadTask status and marking it as completed.

    Args:
        request: The request object
        exc: The exception that was raised
        traceback: The traceback
        upload_task_instance_uuid: The UUID of the UploadTask instance
        step_name: The name of the step that failed
    """

    # Get the upload task instance
    upload_task = api_models.UploadTask.objects.get(uuid=upload_task_instance_uuid)

    # Get the exception class and message
    error_type = exc.__class__.__name__
    error_message = str(exc)

    logger.warning(f"Error during {step_name}: {error_type} - {error_message}")

    # Update the task status
    upload_task.status = "FAILED"
    upload_task.log = error_message
    upload_task.save()

    # Returning None or False will prevent the chain from continuing
    return None


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
    # Make sure the upload task does not have pending before starting the async queries.
    task = api_models.UploadTask.objects.get(uuid=upload_task_instance_uuid)
    task.progress = "10"
    task.log = "Upload task started."
    task.save()

    # Add error handling to each task using .on_error()
    workflow = chain(
        generate_xml_file_task.s(upload_task_instance_uuid).on_error(
            handle_task_error.s(upload_task_instance_uuid, "generate_xml")
        ),
        validate_xml_file_task.s(bro_username, bro_password).on_error(
            handle_task_error.s(upload_task_instance_uuid, "validate_xml")
        ),
        deliver_xml_file_task.s().on_error(
            handle_task_error.s(upload_task_instance_uuid, "deliver_xml")
        ),
        check_delivery_status_task.s().on_error(
            handle_task_error.s(upload_task_instance_uuid, "check_delivery")
        ),
    )
    workflow.apply_async()


@shared_task(queue="upload")
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


@shared_task(queue="upload")
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


@shared_task(queue="upload")
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
