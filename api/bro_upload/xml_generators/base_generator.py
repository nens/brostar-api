from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

from lxml import etree
from lxml.etree import _Element, tostring

from .. import config

class XMLGenerator(ABC):
    """Handles the creation of the XML files.

    This baseclass is inherited by the XML Generators per request type.

    """

    def __init__(
        self,
        request_type: str,
        metadata: Dict[str, Any],
        sourcedocs_data: Dict[str, Any],
    ) -> None:
        self.request_type = request_type
        self.metadata = metadata
        self.sourcedocs_data = sourcedocs_data
        self.namespace = None
        self.xsi_schema_location = None

    def create_xml_file(self) -> Tuple[_Element, str]:
        """Generates the XML file, based on the provided request_type, metadata and sourcedocs_data"""
        self._setup_xml_tree()
        self._add_metadata()

        self.source_document = etree.Element("sourceDocument")
        self._create_sourcedocument()
        self.xml_tree.append(self.source_document)

        self.xml_tree = etree.ElementTree(self.xml_tree)
        xml_string = tostring(self.xml_tree, encoding="utf-8", xml_declaration=True)

        return xml_string
    
    def _setup_xml_tree(self) -> None:
        """Sets up the basis of the XML File, consisting of the declaration urls."""
        self.xml_tree = etree.Element(
            self.request_type,
            nsmap=self.namespace,
        )

        if self.xsi_schema_location:
            self.xml_tree.set(
                "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
                self.xsi_schema_location,
            )
    
    def _add_metadata(self):
        """Fills in the metadata (all information between the declaration sourcedocs."""
        
        metadata_options = [
            "requestReference",
            "deliveryAccountableParty",
            "broId",
            "qualityRegime",
        ]

        for metadata_field in metadata_options:
            if metadata_field in self.metadata:
                request_reference = etree.SubElement(
                    self.xml_tree,
                    f'{{{config.brocom}}}{metadata_field}',
                )
                request_reference.text = self.metadata[metadata_field]

    
    @abstractmethod
    def _create_sourcedocument(self):
        """Creates the sourcedocs XML structure."""
        pass
