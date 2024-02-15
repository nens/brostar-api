import requests
from lxml.etree import _Element
from typing import Dict, Any

from django.conf import settings

def validate_xml_file(xml_file: _Element, bro_username: str, bro_password:str, project_number:str) -> Dict[str, Any]:
    """Validates a XML file with the Bronhouderportaal api."""
    
    if settings.ENVIRONMENT == "productie": 
        url = f"{settings.BRONHOUDERSPORTAAL_URL}/api/v2/{project_number}/validatie"
    elif settings.ENVIRONMENT == "development":
        url = f"{settings.BRONHOUDERSPORTAAL_URL}/api/v2/validatie"
    
    try:
        r = requests.post(
            url=url,
            data=xml_file,
            headers={"Content-Type": "application/xml"},
            auth=(bro_username, bro_password)
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Request error: {e}")
        
