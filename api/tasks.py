import logging

from celery import shared_task
from . import models
from .bro_import import bulk_import


@shared_task
def import_bro_data_task(import_task_instance_uuid):
    """Celery task that imports the data based on a KvK and BRO Domain.

    It is called when a valid POST request is done on the import-task endpoint is done.
    The BulkImporter class is used to handle the whole proces.
    The status and logging of the process can be found in the ImportTask instance.
    """
    # Lookup and update the import task instance
    import_task_instance = models.ImportTask.objects.get(uuid=import_task_instance_uuid)
    import_task_instance.status = "PROCESSING"
    import_task_instance.save()
    
    # Initialize and run importer
    importer = bulk_import.BulkImporter(import_task_instance_uuid)
    
    try:
        importer.run()
    except Exception as e:
        import_task_instance.log = e
        import_task_instance.status = "FAILED"
        import_task_instance.save()

