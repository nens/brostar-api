import requests

from django.conf import settings
from .. import models

class FetchBROIDsError(Exception):
    """Custom exception for errors during BRO IDs fetching."""

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
        """ Handles the complete import process.
        """
        bro_ids = self._fetch_bro_ids()
        print(bro_ids)

    def _fetch_bro_ids(self) -> list:
        """Fetch BRO IDs from the provided URL.

        Returns:
            dict: The fetched BRO IDs.
        """
        url = self._create_bro_ids_import_url()

        try:
            r = requests.get(url)
            r.raise_for_status() 
            bro_ids = r.json()["broIds"]
            
            return bro_ids
        
        except requests.RequestException as e:
            raise FetchBROIDsError(f"Error fetching BRO IDs from {url}: {e}") from e
        
    def _create_bro_ids_import_url(self) -> str:
        """ Creates the import url for a given bro object type and kvk combination.       
        """
        bro_object_type = self.bro_object_type.lower()
        url = f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/{bro_object_type}/v1/bro-ids?bronhouder={self.kvk_number}"
        return url
    
    


