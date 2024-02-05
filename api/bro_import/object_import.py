from abc import ABC, abstractmethod

class ObjectImporter(ABC):
    """ Imports the BRO data based on the bro_id of the object.

    The run method should be called after initializing. It handles:

        1) Creation of URL
        2) Download of the XML
        3) Translation from XML to json
        4) Save actions into the database
    """
    def __init__(self, bro_id):
        self.bro_id = bro_id

    def run(self):
        url = self._create_download_url()
        xml_file = self._download_xml(url)
        json_data = self._convert_xml_to_json(xml_file)

        self._save_data(json_data)
    
    def _create_download_url(self):
        pass

    def _download_xml(self, url):
        pass

    def _convert_xml_to_json(self, xml_file):
        pass

    @abstractmethod
    def _save_data(self):
        pass
    
class GMNObjectImporter(ObjectImporter):
    pass

class GMWObjectImporter(ObjectImporter):
    pass

class GLDObjectImporter(ObjectImporter):
    pass

class FRDObjectImporter(ObjectImporter):
    pass
