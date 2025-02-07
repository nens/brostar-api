import logging

from celery import shared_task

from api.bro_import import bulk_import
from api.bro_upload.gar_bulk_upload import GARBulkUploader
from api.bro_upload.gld_bulk_upload import GLDBulkUploader
from api.bro_upload.object_upload import BRODelivery

logger = logging.getLogger(__name__)


@shared_task
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


@shared_task
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


@shared_task
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


@shared_task
def gld_bulk_upload_task(
    bulk_upload_instance_uuid: str,
    measurement_tvp_file_uuid: str,
    bro_username: str,
    bro_password: str,
) -> None:
    """Celery task that handles the bulk upload for GAR data after a POST on the bulkupload endpoint."""
    try:
        uploader = GLDBulkUploader(
            bulk_upload_instance_uuid,
            measurement_tvp_file_uuid,
            bro_username,
            bro_password,
        )
        uploader.process()
    except Exception as e:
        logger.exception(e)
