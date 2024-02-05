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
    
    # Lookup the right importer class to initiate
    domain_importer_mapping = {
        "GMN":bro_import.GMNImporter,
        "GMW":bro_import.GMWImporter,
        "GLD":bro_import.GLDImporter,
        "FRD":bro_import.FRDImporter,
    }

    bro_domain = import_task_instance.bro_domain
    importer_class = domain_importer_mapping[bro_domain]

    # Initiate the importer
    importer = importer_class(import_task_instance_uuid)
    
    try:
        importer.run()
    except Exception as e:
        import_task_instance.log = e
        import_task_instance.status = "FAILED"
        import_task_instance.save()

