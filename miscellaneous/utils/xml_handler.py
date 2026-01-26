
import xml.etree.ElementTree as ET
import logging
import re

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load the XML
tree = ET.parse("input.xml")
root = tree.getroot()

# Define namespaces used in your XML
NAMESPACE = {
    "brocom": "http://www.broservices.nl/xsd/brocommon/3.0"
}
BRO_DOMAIN_XML_ID = ""
KVK_XML_ID = ".//brocom:deliveryAccountableParty"

class XMLHandler:
    bro_domain = None
    kvk_number = None

    def __init__(self, path_to_xml, kvk_number = None, project_number = None):
        self._root(path_to_xml)
        self._bro_domain()
        self._kvk_number(kvk_number)
        self.project_number = project_number

    def _root(self, path_to_xml):
        tree = ET.parse(path_to_xml)
        self.root = tree.getroot()

    def _bro_domain(self):
        logger.info(self.bro_domain)
        self.bro_domain = re.search(r"/is([^/]+)/", self.root.tag.split("}")[0][1:]).group(1)
        logger.info(self.bro_domain)

    def _kvk_number(self, kvk_number):
        elem = self.root.find(KVK_XML_ID, NAMESPACE)
        if elem is not None:
            self.kvk_number = elem.text
        if kvk_number is not None:
            self.kvk_number = kvk_number

    def xml_to_bro(self):
        pass
        
    




