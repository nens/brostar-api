from . import mappings

class Delivery:
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

    def __init__(self, upload_task_instance: str) -> None:
        self.upload_task_instance = upload_task_instance
        self.bro_domain = self.upload_task_instance.bro_domain
        self.registration_type = self.upload_task_instance.registration_type
        self.request_type = self.upload_task_instance.registration_type
        self.sourcedocument_data = self.upload_task_instance.sourcedocument_data
        self.xml_generator_class = mappings.xml_generator_mapping.get(self.registration_type)
        
    def process(self) -> None:
        pass
