import requests
from lxml.etree import _Element
from typing import Dict, Any

from django.conf import settings

#TODO: add token and projectnummer to this function
def validate_xml_file(xml_file: _Element) -> Dict[str, Any]:
    """Validates a XML file with the Bronhouderportaal api."""
    url = f"{settings.BRONHOUDERSPORTAAL_URL}/api/v2/validatie"

    try:
        r = requests.post(
            url=url,
            data=xml_file,
            headers={"Content-Type": "application/xml"},
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Request error: {e}")
        
