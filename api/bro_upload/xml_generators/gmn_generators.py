from lxml import etree
from lxml.etree import _Element, tostring

from .. import config
from .base_generator import XMLGenerator

class GMNStartregistration(XMLGenerator):
    """Generates a XML file for the 01_GMN_StartRegistration."""
    def __init__(self, request_type: str, metadata: dict, srcdocdata: dict) -> None:
        super().__init__(request_type, metadata, srcdocdata)
        self.namespace = config.declaration_mapping[self.request_type]
        self.xsi_schema_location = config.xsi_schemalocation
        self.id_count = 1
    
    def _create_sourcedocument(self):
        """Example XML for register:
        https://www.bro-productomgeving.nl/__attachments/159095997/01_GMN_StartRegistration.xml?inst-v=6362ee09-a77d-4052-8ab8-caf3a373ad16
        """
        # Create main sourcedocs element
        main_element = etree.Element(
            f'{{{config.gmn}}}GMN_StartRegistration'
        )
        main_element.set(
            f"{{{config.gml}}}id", f"id_000{self.id_count}"
        )
        self.id_count += 1

        # Create object id accountable party element
        object_id_accountable_party_element = etree.SubElement(
            main_element,
            "objectIdAccountableParty",
        )
        object_id_accountable_party_element.text = self.sourcedocs_data["objectIdAccountableParty"]

        # Create name element
        name_element = etree.SubElement(
            main_element,
            "name",
        )
        name_element.text = self.sourcedocs_data["name"]
        
        # Create delivery context element

        # Create monitoring purpose element

        # Create groundwater aspect element


        # Add startregistration to sourcedocs
        self.source_document.append(main_element)
