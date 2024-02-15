from . import mappings
from lxml.etree import _Element

from . import utils

class XMLValidationError(Exception):
    """Exception raised when XML validation fails."""
    pass

class BRODelivery:
    """ Handles the complete process of uploading data to the BRO.
    
    During the initialization, a XML-generator class is defined based on the provided registration_type.
    This class instance is then used to create the XML file for the Delivery.
    The rest of the delivery process is handled by this class. 
    
    The steps of the complete process are:
        1) Generation of the XML File.
        2) Validation of the XML File with the BRO webservice.
        3) Delivery of the XML file to the BRO.
        4) The check of the delivery status.
        5) Finalization of the whole process.
    """

    def __init__(self, upload_task_instance: str, bro_username: str, bro_password: str, project_number: str) -> None:
        self.upload_task_instance = upload_task_instance
        self.bro_username = bro_username
        self.bro_password = bro_password
        self.project_number = project_number
        self.bro_domain = self.upload_task_instance.bro_domain
        self.registration_type = self.upload_task_instance.registration_type
        self.request_type = self.upload_task_instance.registration_type
        self.metadata = self.upload_task_instance.metadata
        self.sourcedocument_data = self.upload_task_instance.sourcedocument_data
        self.xml_generator_class = mappings.xml_generator_mapping.get(self.registration_type)
        
    def process(self) -> None:
        xml_file = self._generate_xml_file()
        
        self._validate_xml_file(xml_file)
        self._deliver_xml_file(xml_file)
        self._check_delivery()
        
        
    def _generate_xml_file(self) -> _Element:
        try:
            generator = self.xml_generator_class(self.request_type, self.metadata, self.sourcedocument_data)
            return generator.create_xml()

        except Exception as e:
            raise RuntimeError(f"Error generating XML file: {e}") from e
        
    def _validate_xml_file(self, xml_file) -> None:
        validation_response = utils.validate_xml_file(xml_file, self.bro_username, self.bro_password, self.project_number)
        
        if validation_response["status"] != "VALIDE":
            raise XMLValidationError(f"Errors while validating the XML file: {validation_response['errors']}")
        else:
            return

    def _deliver_xml_file(self, xml_file):
        pass

    def _check_delivery(self):
        pass

