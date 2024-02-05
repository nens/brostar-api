import logging

from celery import shared_task
from . import models
from .bro_import import bro_import


@shared_task
def import_bro_data_task(import_task_instance_uuid):
    """ Tasks that runs a POST request on the import-task endpoint.

    It uses the BROImporter class to handle the whole process.
    The status and logging of the process can be found in the ImportTask instance.
    """
    import_task_instance = models.ImportTask.objects.get(uuid=import_task_instance_uuid)
    import_task_instance.status = "PROCESSING"
    import_task_instance.save()

    importer = bro_import.BROImporter(import_task_instance_uuid)
    
    try:
        bro_ids = importer.fetch_bro_ids()
    except bro_import.FetchBROIDsError as e:
        import_task_instance.log = e
        import_task_instance.status = "FAILED"
        import_task_instance.save()

    print(bro_ids)