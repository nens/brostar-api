import logging

from celery import shared_task

from .bro_import import bulk_import
from .bro_upload.delivery import BRODelivery

logger = logging.getLogger(__name__)


@shared_task
def import_bro_data_task(import_task_instance_uuid: str) -> None:
    """Celery task that imports the data based on a KvK and BRO Domain.

    It is called when a valid POST request is done on the importtask endpoint is done.
    The BulkImporter class is used to handle the whole proces.
    The status and logging of the process can be found in the ImportTask instance.
    """
    # Initialize and run importer
    importer = bulk_import.BulkImporter(import_task_instance_uuid)
    importer.run()


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
    # Initialize and run importer
    uploader = BRODelivery(upload_task_instance_uuid, bro_username, bro_password)
    uploader.process()
