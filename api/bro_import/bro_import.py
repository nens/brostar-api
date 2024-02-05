from .. import models
from .. import utils


class BROImporter:
    def __init__(self, import_task_instance_uuid):
        """Initializes an Importer for an import task.

        Relevant information is:
            1) the BRO object type
            2) the KvK number of the organisation.

        """
        self.import_task_instance = models.ImportTask.objects.get(
            uuid=import_task_instance_uuid
        )
        self.bro_object_type = self.import_task_instance.bro_object_type
        self.organisation = self.import_task_instance.organisation
        self.kvk_number = self.organisation.kvk_number

    def run(self):
        url = utils.create_bro_ids_import_url(
            self.bro_object_type,
        )
