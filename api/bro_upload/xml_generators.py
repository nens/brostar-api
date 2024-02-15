from abc import ABC
from typing import Dict, Any, Tuple

from lxml import etree
from lxml.etree import _Element

class XMLGenerator(ABC):
    """ Handles the creation of the XML files.
    
    This baseclass is inherited by the XML Generators per request type.
    
    """
    def __init__(self, request_type: str, metadata: Dict[str, Any], sourcedocs_data: Dict[str, Any]) -> None:
        self.request_type = request_type
        self.metadata = metadata
        self.sourcedocs_data = sourcedocs_data

    def create_xml(self) -> Tuple[_Element, str]:
        #TODO: write this 'main' method and all the other methods. check https://github.com/nens/bro-exchange/blob/main/bro_exchange/broxml/frd/requests.py for inspiration
        return (etree.Element(
            "test",
        ), "filename")

class GMNStartregistration(XMLGenerator):
    """Generates a XML file for the 01_GMN_StartRegistration
    """
    pass