import requests
from abc import ABC, abstractmethod

from django.conf import settings
from .. import models

class FetchBROIDsError(Exception):
    """Custom exception for errors during BRO IDs fetching."""

class BROImporter(ABC):
    """ Imports data from the BRO 'uitgifteservice' and saves it into the Django datamodel.
    
    It first fetches all BRO id's for the given BRO object type.
    Then loops over all id's to import the data if its object.
    Saves the data in the corresponding datamodel in this project.
    """

    def __init__(self, import_task_instance_uuid):
        self.import_task_instance = models.ImportTask.objects.get(
            uuid=import_task_instance_uuid
        )
        self.bro_domain = self.import_task_instance.bro_domain
        self.organisation = self.import_task_instance.organisation
        self.kvk_number = self.organisation.kvk_number

    def run(self):
        """ Handles the complete import process.
        """
        bro_ids = self._fetch_bro_ids()
        
        for bro_id in bro_ids:
            self._import_bro_object_data(bro_id)

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
        bro_domain = self.bro_domain.lower()
        url = f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/{bro_domain}/v1/bro-ids?bronhouder={self.kvk_number}"
        return url
    
    @abstractmethod
    def _import_bro_object_data(self):
        """ Handles the import of the object specific data from the BRO.
        
        This abstract method varies for each BRO object type, but the generic setup is:
            1) generate the url
            2) fetch the data
            3) and save the data to the database.
        """
    
    


