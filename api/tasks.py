import logging
from logging import getLogger

from celery import chain, chord, group, shared_task
from django.db.models import F

import api.models as api_models
from api.bro_import import bulk_import, config
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
        upload_task_instance.save(update_fields=["status", "log"])
        logger.info(f"Error generating XML file: {generator.error_message}")
        return None

    validation_response = utils.validate_xml_file(
        xml,
        bro_username,
        bro_password,
        upload_task_instance.project_number,
    )

    # Clean up memory
    del generator
    del xml

    context = {
        "upload_task_instance_uuid": upload_task_instance_uuid,
        "bro_password": bro_password,
        "bro_username": bro_username,
    }

    if validation_response["status"] != "VALIDE" and validation_response["errors"] != [
        "U bent niet als dataleverancier van dit object geregistreerd."
    ]:
        upload_task_instance.progress = 50.0
        upload_task_instance.log = "XML is niet geldig"
        upload_task_instance.status = "FAILED"
        upload_task_instance.bro_errors = validation_response["errors"]
        upload_task_instance.save(
            update_fields=["progress", "log", "status", "bro_errors"]
        )
        logger.info(
            f"Errors tijdens het valideren van het XML bestand: {validation_response['errors']}"
        )
        return None
    elif validation_response.get("errors") == [
        "U bent niet als dataleverancier van dit object geregistreerd."
    ]:
        upload_task_instance.bro_errors = validation_response["errors"]

    upload_task_instance.progress = 50.0
    upload_task_instance.log = "XML is succesvol gevalideerd"
    upload_task_instance.save(update_fields=["progress", "log", "bro_errors"])
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
        upload_task_instance.save(update_fields=["status", "log"])
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
        upload_task_instance.save(update_fields=["status", "log"])
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
        upload_task_instance.save(update_fields=["status", "log"])
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
    upload_task_instance.save(update_fields=["progress", "log", "bro_delivery_url"])
    context["delivery_url"] = delivery_url
    return context


class DeliveryNotReadyError(Exception):
    """Raised when delivery status check should be retried"""

    pass


@shared_task(
    bind=True,
    queue="upload",
    autoretry_for=(DeliveryNotReadyError,),
    retry_backoff=5,  # Factor in seconds (first retry: 5s, second: 10s, third: 20s, etc.)
    retry_jitter=False,  # Set False to disable randomization (use exact values: 5s, 10s, 20s)
    max_retries=10,  # Total retry time will be around 5s + 10s + 20s + 40s + 80s + 160s + 320s + 640s + 1280s + 2560s = ~1.5 hours
)
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
        upload_task_instance.log = "Error after delivery"
        upload_task_instance.bro_errors = f"{errors}"
        upload_task_instance.save(update_fields=["status", "log", "bro_errors"])
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
        upload_task_instance.save(update_fields=["progress", "log", "bro_id", "status"])

        organisation = upload_task_instance.data_owner
        if organisation is not None:
            organisation.request_count += 1
            organisation.save(update_fields=["request_count"])

        return context

    # If not completed and not errors, raise exception to trigger auto-retry
    retry_count = self.request.retries + 1
    total_time = sum(5 * (2 ** (i - 1)) for i in range(retry_count))
    unit = "seconds"

    if total_time > 120:
        total_time = round(total_time / 60, 1)
        unit = "minutes"

    upload_task_instance.log = f"XML aangeleverd: na status controle ({retry_count} - {total_time} {unit}) nog geen uitslag."
    upload_task_instance.save(update_fields=["log"])

    # This will be called automatically when max_retries is exceeded
    if self.request.retries >= self.max_retries:
        upload_task_instance.status = "UNFINISHED"
        upload_task_instance.log = "Na 1,5 uur is er nog geen resultaat bekend. Controleer het later handmatig."
        upload_task_instance.progress = 95.0
        upload_task_instance.save(update_fields=["status", "log", "progress"])
        return  # Don't raise, task ends here

    # Raise custom exception to trigger Celery's automatic retry with backoff
    raise DeliveryNotReadyError(f"Delivery not ready after {retry_count} attempts")


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
    upload_task.bro_errors = str([convert_error_to_bro_error(error_message)])
    upload_task.save(update_fields=["status", "log", "bro_errors"])

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
    task.save(update_fields=["progress", "log"])

    # Add error handling to each task using .on_error()
    workflow = chain(
        validate_xml_file_task.s(upload_task_instance_uuid, bro_username, bro_password)
        .set(queue="upload")
        .on_error(handle_task_error.s(upload_task_instance_uuid, "validate_xml")),
        deliver_xml_file_task.s()
        .set(queue="upload")
        .on_error(handle_task_error.s(upload_task_instance_uuid, "deliver_xml")),
        check_delivery_status_task.s()
        .set(queue="upload")
        .on_error(handle_task_error.s(upload_task_instance_uuid, "check_delivery")),
    )
    workflow.apply_async(queue="upload")


@shared_task(queue="upload")
def gar_bulk_upload_task(
    bulk_upload_instance_uuid: str,
    fieldwork_upload_file_uuid: str,
    lab_upload_file_uuid: str,
) -> None:
    """Celery task that handles the bulk upload for GAR data after a POST on the bulkupload endpoint."""
    try:
        logger.info(
            f"Starting bulk upload from task with {bulk_upload_instance_uuid}, {fieldwork_upload_file_uuid} and {lab_upload_file_uuid}"
        )
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


# ---------------------------------------------------------------------------
# Async bulk import – chord-based fan-out
# ---------------------------------------------------------------------------

KNOWN_BRO_DOMAINS = set(config.object_importer_mapping.keys())


@shared_task(queue="default")
def fetch_bro_ids_and_dispatch_task(import_task_instance_uuid: str) -> None:
    """Entry point for the new async bulk import flow.

    Fetches all BRO IDs for the domain/KVK stored in the ImportTask, then
    dispatches a Celery chord:
    - header: one ``import_single_object_task`` per BRO ID
    - callback: ``finalize_bulk_import_task`` that marks the ImportTask done

    The original ``import_bro_data_task`` is kept intact for backward
    compatibility; new ImportTask signals call this task instead.
    """
    import_task = api_models.ImportTask.objects.get(uuid=import_task_instance_uuid)
    import_task.status = "PROCESSING"
    import_task.progress = 0.0
    import_task.log = "Fetching BRO IDs…"
    import_task.save(update_fields=["status", "progress", "log"])

    try:
        importer = bulk_import.BulkImporter(import_task_instance_uuid)
        url = importer._create_bro_ids_import_url()
        bro_ids = importer._fetch_bro_ids(url)
    except Exception as e:
        import_task.status = "FAILED"
        import_task.log = f"Failed to fetch BRO IDs: {e}"
        import_task.save(update_fields=["status", "log"])
        logger.info(f"fetch_bro_ids_and_dispatch_task failed: {e}")
        return

    total = len(bro_ids)
    if total == 0:
        import_task.status = "COMPLETED"
        import_task.progress = 100.0
        import_task.log = "No BRO IDs found – nothing to import."
        import_task.save(update_fields=["status", "progress", "log"])
        return

    import_task.log = f"Dispatching {total} import tasks…"
    import_task.save(update_fields=["log"])

    force = import_task.log == "FORCE"
    data_owner_id = str(import_task.data_owner_id)
    bro_domain = import_task.bro_domain

    # GLD imports make many sub-requests per object and need a dedicated
    # rate-limited queue to avoid flooding the BRO API when parallel imports run.
    task_sig = (
        import_single_gld_object_task
        if bro_domain == "GLD"
        else import_single_object_task
    )

    header = group(
        task_sig.s(
            bro_id,
            bro_domain,
            data_owner_id,
            str(import_task_instance_uuid),
            force,
            total,
        )
        for bro_id in bro_ids
    )
    callback = finalize_bulk_import_task.s(str(import_task_instance_uuid))
    chord(header, callback).apply_async()


def _run_single_object_import(
    bro_id: str,
    bro_domain: str,
    data_owner_id: str,
    import_task_instance_uuid: str,
    force: bool,
    total: int,
) -> dict:
    """Shared implementation for both object import tasks."""
    from api.models import ImportTask, Organisation

    try:
        importer_class = config.object_importer_mapping.get(bro_domain)
        if importer_class is None:
            return {
                "bro_id": bro_id,
                "success": False,
                "error": f"Unknown domain: {bro_domain}",
            }

        data_owner = Organisation.objects.get(uuid=data_owner_id)
        importer = importer_class(bro_id, data_owner)
        importer.run(force=force)

        # Atomically increment progress so concurrent tasks don't overwrite each other
        increment = 100.0 / total
        ImportTask.objects.filter(uuid=import_task_instance_uuid).update(
            progress=F("progress") + increment
        )

        logger.info(f"Imported {bro_id} successfully.")
        return {"bro_id": bro_id, "success": True}

    except Exception as e:
        logger.info(f"Error importing {bro_id}: {e}")
        return {"bro_id": bro_id, "success": False, "error": str(e)}


@shared_task(queue="default", rate_limit="20/m")
def import_single_object_task(
    bro_id: str,
    bro_domain: str,
    data_owner_id: str,
    import_task_instance_uuid: str,
    force: bool,
    total: int,
) -> dict:
    """Import a single non-GLD BRO object and return a result dict.

    This task is designed to never raise so that the chord callback always
    fires, even when individual objects fail.

    Rate-limited to 20/min per worker to stay within BRO API tolerances.
    Increment is calculated per-task so progress stays accurate regardless of
    task ordering.
    """
    return _run_single_object_import(
        bro_id, bro_domain, data_owner_id, import_task_instance_uuid, force, total
    )


@shared_task(queue="gld_import", rate_limit="3/m")
def import_single_gld_object_task(
    bro_id: str,
    bro_domain: str,
    data_owner_id: str,
    import_task_instance_uuid: str,
    force: bool,
    total: int,
) -> dict:
    """Import a single GLD object and return a result dict.

    GLD imports make many sub-requests per object (one observation summary +
    one request per observation), so they are rate-limited more aggressively
    than other domains to avoid hitting the BRO API rate limit when multiple
    GLD imports run in parallel.

    Run workers for this queue with low concurrency, e.g.:
        celery -A brostar_api worker -Q gld_import --concurrency=1
    """
    return _run_single_object_import(
        bro_id, bro_domain, data_owner_id, import_task_instance_uuid, force, total
    )


@shared_task(queue="default")
def finalize_bulk_import_task(
    results: list[dict], import_task_instance_uuid: str
) -> None:
    """Chord callback: summarise results and mark ImportTask as COMPLETED or FAILED."""
    import_task = api_models.ImportTask.objects.get(uuid=import_task_instance_uuid)

    successes = sum(1 for r in results if r and r.get("success"))
    failures = len(results) - successes
    failed_ids = [r["bro_id"] for r in results if r and not r.get("success")]

    if successes == 0 and failures > 0:
        import_task.status = "FAILED"
    else:
        import_task.status = "COMPLETED"

    import_task.progress = 100.0
    summary = f"Import voltooid: {successes} geslaagd, {failures} mislukt."
    if failed_ids:
        summary += f" Mislukte IDs: {', '.join(failed_ids[:20])}"
        if len(failed_ids) > 20:
            summary += f" … en {len(failed_ids) - 20} meer."
    import_task.log = summary
    import_task.save(update_fields=["status", "progress", "log"])
    logger.info(f"finalize_bulk_import_task: {summary}")


# ---------------------------------------------------------------------------
# Individual object import
# ---------------------------------------------------------------------------


@shared_task(queue="default")
def import_object_task(object_import_task_uuid: str) -> None:
    """Import a single BRO object tracked by an ObjectImportTask instance.

    Triggered by ``ObjectImportTaskViewSet.create()``.  Updates
    ``ObjectImportTask.status`` and ``ObjectImportTask.log`` on completion.
    """
    obj_task = api_models.ObjectImportTask.objects.get(uuid=object_import_task_uuid)
    obj_task.status = "PROCESSING"
    obj_task.save(update_fields=["status"])

    try:
        importer_class = config.object_importer_mapping.get(obj_task.bro_domain)
        if importer_class is None:
            raise ValueError(
                f"No importer available for domain '{obj_task.bro_domain}'."
            )

        importer = importer_class(obj_task.bro_id, obj_task.data_owner)
        importer.run(force=obj_task.force)

        obj_task.status = "COMPLETED"
        obj_task.log = f"Import van {obj_task.bro_id} geslaagd."
        logger.info(f"import_object_task: {obj_task.bro_id} completed.")

    except Exception as e:
        obj_task.status = "FAILED"
        obj_task.log = str(e)
        logger.info(f"import_object_task: {obj_task.bro_id} failed – {e}")

    obj_task.save(update_fields=["status", "log"])
