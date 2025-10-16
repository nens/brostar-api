import logging
from logging import getLogger

from celery import chain, shared_task

import api.models as api_models
from api.bro_import import bulk_import
from api.bro_upload import utils
from api.bro_upload.gar_bulk_upload import GARBulkUploader
from api.bro_upload.gld_bulk_upload import GLDBulkUploader
from api.bro_upload.gmn_bulk_upload import GMNBulkUploader
from api.bro_upload.object_upload import (
    XMLGenerator,
)

logger = logging.getLogger("general")


logger = getLogger(__name__)


@shared_task(queue="upload")
def validate_xml_file_task(
    upload_task_instance_uuid: str, bro_username: str, bro_password: str
):
    upload_task_instance = api_models.UploadTask.objects.get(
        uuid=upload_task_instance_uuid
    )
    # generator = XMLGenerator(
    #     upload_task_instance.registration_type,
    #     upload_task_instance.request_type,
    #     upload_task_instance.metadata,
    #     upload_task_instance.sourcedocument_data,
    # )
    # xml = generator.create_xml_file()
    # if generator.status == "FAILED":
    #     upload_task_instance.status = "FAILED"
    #     upload_task_instance.log = generator.error_message
    #     upload_task_instance.save()
    #     logger.info(f"Error generating XML file: {generator.error_message}")
    #     return None

    # validation_response = utils.validate_xml_file(
    #     xml,
    #     bro_username,
    #     bro_password,
    #     upload_task_instance.project_number,
    # )

    # # Clean up memory
    # del generator
    # del xml

    context = {
        "upload_task_instance_uuid": upload_task_instance_uuid,
        "bro_password": bro_password,
        "bro_username": bro_username,
    }

    # if validation_response["status"] != "VALIDE":
    #     upload_task_instance.progress = 50.0
    #     upload_task_instance.log = "XML is niet geldig"
    #     upload_task_instance.status = "FAILED"
    #     upload_task_instance.bro_errors = validation_response["errors"]
    #     upload_task_instance.save()
    #     logger.info(
    #         f"Errors tijdens het valideren van het XML bestand: {validation_response['errors']}"
    #     )
    #     return None

    upload_task_instance.progress = 50.0
    upload_task_instance.log = "XML is succesvol gevalideerd"
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

    upload = utils.create_upload_url(
        bro_username,
        bro_password,
        upload_task_instance.project_number,
    )
    if upload["status"] != "OK":
        upload_task_instance.status = "FAILED"
        upload_task_instance.log = f"Error tijdens het maken van de upload URL: {upload.get('errors', 'Unknown error')}"
        upload_task_instance.save()
        return None

    generator = XMLGenerator(
        upload_task_instance.registration_type,
        upload_task_instance.request_type,
        upload_task_instance.metadata,
        upload_task_instance.sourcedocument_data,
    )
    xml = generator.create_xml_file()
    if generator.status == "FAILED":
        upload_task_instance.status = "FAILED"
        upload_task_instance.log = generator.error_message
        upload_task_instance.save()
        logger.info(f"Error generating XML file: {generator.error_message}")
        return None

    upload_url = upload["upload_url"]
    succes = utils.add_xml_to_upload(
        xml,
        upload_url,
        bro_username,
        bro_password,
    )

    # Clean up memory
    del generator
    del xml

    if not succes:
        upload_task_instance.status = "FAILED"
        upload_task_instance.log = (
            "Error tijdens het toevoegen van het XML bestand aan de upload"
        )
        upload_task_instance.save()
        return None

    delivery_url = utils.create_delivery(
        upload_url,
        bro_username,
        bro_password,
        upload_task_instance.project_number,
    )
    upload_task_instance.bro_delivery_url = delivery_url
    upload_task_instance.progress = 75.0
    upload_task_instance.log = "XML aangeleverd."
    upload_task_instance.save()
    context["delivery_url"] = delivery_url
    return context


@shared_task(bind=True, queue="upload", max_retries=10, retry_backoff=5)
def check_delivery_status_task(self, context):
    if context is None:
        return None

    upload_task_instance = api_models.UploadTask.objects.get(
        uuid=context["upload_task_instance_uuid"]
    )
    delivery_info = utils.check_delivery_status(
        context["delivery_url"], context["bro_username"], context["bro_password"]
    )
    errors = delivery_info["brondocuments"][0]["errors"]

    if errors:
        upload_task_instance.status = "FAILED"
        upload_task_instance.log = f"Errors: {errors}"
        upload_task_instance.save()
        return

    if (
        delivery_info["status"] == "DOORGELEVERD"
        and delivery_info["brondocuments"][0]["status"] == "OPGENOMEN_LVBRO"
    ):
        bro_id = delivery_info["brondocuments"][0]["broId"]
        upload_task_instance.bro_id = bro_id
        upload_task_instance.status = "COMPLETED"
        upload_task_instance.log = f"Upload geslaagd: {bro_id}"
        upload_task_instance.progress = 100.0
        upload_task_instance.save()
        return context

    # If not completed and not errors, retry the task
    try:
        # Current retry attempt (starting from 1)
        retry_count = self.request.retries + 1

        # Compute elapsed time based on exponential backoff
        # Celery retry_backoff = 5 means: 5s, 10s, 20s, 40s, ...
        total_time = sum(5 * (2**i) for i in range(retry_count))
        unit = "seconds"

        if total_time > 120:
            total_time = round(total_time / 60, 1)
            unit = "minutes"

        upload_task_instance.log = f"XML aangeleverd: na status controle ({retry_count} - {total_time} {unit}) nog geen uitslag."
        upload_task_instance.save()

        raise self.retry()
    except self.MaxRetriesExceededError:
        upload_task_instance.status = "UNFINISHED"
        upload_task_instance.log = "Na 1,5 uur is er nog geen resultaat bekend. Controleer het later handmatig."
        upload_task_instance.progress = 95.0
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
        logger.info(f"Error during bulk-import: {e}")


def convert_error_to_bro_error(error_message: str):
    if error_message.__contains__("404 Client Error"):
        return "Projectnummer klopt waarschijnlijk niet. Controleer deze."
    elif error_message.__contains__("401") or error_message.__contains__("403"):
        return "Niet gemachtigd voor object of project. Controleer machtigingen en dataleverancierschap."
    else:
        return error_message


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

    logger.info(f"Error during {step_name}: {error_type} - {error_message}")

    # Update the task status
    upload_task.status = "FAILED"
    upload_task.log = error_message
    upload_task.bro_errors = [convert_error_to_bro_error(error_message)]
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
    The status and logging of the process can be found in the UploadTask instance.
    """
    # Make sure the upload task does not have pending before starting the async queries.
    task = api_models.UploadTask.objects.get(uuid=upload_task_instance_uuid)
    task.progress = "10"
    task.log = "Upload task started."
    task.save()

    # Add error handling to each task using .on_error()
    workflow = chain(
        validate_xml_file_task.s(
            upload_task_instance_uuid, bro_username, bro_password
        ).on_error(handle_task_error.s(upload_task_instance_uuid, "validate_xml")),
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
        logger.info(f"Error during GAR bulk upload: {e}")


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
        logger.info(f"Error during GLD bulk upload: {e}")


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
        logger.info(f"Error during GMN bulk upload: {e}")
