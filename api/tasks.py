from celery import shared_task
from . import models

@shared_task
def import_bro_data_task(import_task_instance_uuid, input_data):
    import_task_instance = models.ImportTask.objects.get(uuid=import_task_instance_uuid)

    import_task_instance.status = "PROCESSING"
    import_task_instance.save()

    