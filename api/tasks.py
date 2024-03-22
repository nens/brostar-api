import logging

import requests
from celery import shared_task

from . import models as api_models
from .bro_import import bulk_import, config
from .bro_upload.delivery import BRODelivery

logger = logging.getLogger(__name__)


@shared_task
def import_bro_data_task(import_task_instance_uuid: str) -> None:
    """Celery task that imports the data based on a KvK and BRO Domain.

    It is called when a valid POST request is done on the importtask endpoint is done.
    The BulkImporter class is used to handle the whole proces.
    The status and logging of the process can be found in the ImportTask instance.
    """
    # Lookup and update the import task instance
    import_task_instance = api_models.ImportTask.objects.get(
        uuid=import_task_instance_uuid
    )
    import_task_instance.status = "PROCESSING"
    import_task_instance.save()

    # Initialize and run importer
    importer = bulk_import.BulkImporter(import_task_instance)

    try:
        importer.run()
        import_task_instance.status = "COMPLETED"
        import_task_instance.save()
    except Exception as e:
        import_task_instance.log = e
        import_task_instance.status = "FAILED"
        import_task_instance.save()


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

    # Lookup and update the import task instance
    upload_task_instance = api_models.UploadTask.objects.get(
        uuid=upload_task_instance_uuid
    )
    upload_task_instance.status = "PROCESSING"
    upload_task_instance.save()

    # Initialize and run importer
    uploader = BRODelivery(upload_task_instance, bro_username, bro_password)

    try:
        # The actual task
        bro_id = uploader.process()

        # Update upload task instance
        upload_task_instance.bro_id = bro_id
        upload_task_instance.status = "COMPLETED"
        upload_task_instance.log = "The upload was done successfully"
        upload_task_instance.save()

        # Start import task to keep the data up to date in the api
        try:
            object_importer_class = config.object_importer_mapping[upload_task_instance.bro_domain]
            object_importer_class(
                bro_domain = upload_task_instance.bro_domain,
                bro_id = upload_task_instance.bro_id,
                data_owner = upload_task_instance.data_owner
            )
        except requests.RequestException as e:
                logger.exception(e)
                raise bulk_import.DataImportError(f"Error while importing data for bro id: {bro_id}: {e}") from e
        

    except Exception as e:
        upload_task_instance.log = e
        upload_task_instance.status = "FAILED"
        upload_task_instance.save()
