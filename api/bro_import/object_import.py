from abc import ABC, abstractmethod
from django.conf import settings

class ObjectImporter(ABC):
    """Imports the BRO data based on the object ID.

    Args:
        bro_domain (str): The BRO domain for the object.
        bro_id (str): The unique identifier of the BRO object.

    The run method should be called after initializing. It handles:

        1) Creation of URL
        2) Download of the XML
        3) Translation from XML to JSON
        4) Save actions into the database
    """
    def __init__(self, bro_domain, bro_id):
        self.bro_domain = bro_domain
        self.bro_id = bro_id
        print('test')

    def run(self):
        url = self._create_download_url()
        # xml_file = self._download_xml(url)
        # json_data = self._convert_xml_to_json(xml_file)

        # self._save_data(json_data)
    
    def _create_download_url(self) -> str:
        """ Creates the import url for a given bro object.       
        """
        bro_domain = self.bro_domain.lower()
        url = f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/{bro_domain}/v1/objects/{self.bro_id}?fullHistory=ja"
        return url

    def _download_xml(self, url):
        pass

    def _convert_xml_to_json(self, xml_file):
        pass

    @abstractmethod
    def _save_downloaded_data(self):
        pass
    
class GMNObjectImporter(ObjectImporter):
    def _save_downloaded_data(self):
        pass

class GMWObjectImporter(ObjectImporter):
    pass

class GLDObjectImporter(ObjectImporter):
    pass

class FRDObjectImporter(ObjectImporter):
    pass
