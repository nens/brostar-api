import requests
import json
import traceback

from typing import Dict, Any

from django.conf import settings


def validate_xml_file(
    xml_file: bytes, bro_username: str, bro_password: str, project_number: str
) -> Dict[str, Any]:
    """Validates a XML file with the Bronhouderportaal api."""
    url = f"{settings.BRONHOUDERSPORTAAL_URL}/api/v2/{project_number}/validatie"

    try:
        r = requests.post(
            url=url,
            data=xml_file,
            headers={"Content-Type": "application/xml"},
            auth=(bro_username, bro_password),
        )
        r.raise_for_status()

        return r.json()

    except requests.RequestException as e:
        traceback.print_exc()
        raise RuntimeError(f"Validate xml error: {e}")


def create_upload_url(bro_username: str, bro_password: str, project_number: str) -> str:
    """POST to the BRO api to receive an upload id, which is step 1 of 3 in the upload process."""
    url = f"{settings.BRONHOUDERSPORTAAL_URL}/api/v2/{project_number}/uploads"

    try:
        r = requests.post(
            url,
            headers={"Content-Type": "application/xml"},
            auth=(bro_username, bro_password),
        )
        r.raise_for_status()
        upload_url = r.headers["Location"]

        return upload_url

    except requests.RequestException as e:
        traceback.print_exc()
        raise RuntimeError(f"Create upload url error: {e}")


def add_xml_to_upload(
    xml_file: str,
    upload_url: str,
    bro_username: str,
    bro_password: str,
) -> str:
    """Add the XML to the upload request, which is step 2 of 3 in the upload process."""

    upload_url = f"{upload_url}/brondocumenten"

    try:
        r = requests.post(
            upload_url,
            headers={"Content-Type": "application/xml"},
            auth=(bro_username, bro_password),
            data=xml_file,
            params={"filename": f"BROHub request"},
        )
        r.raise_for_status()
        return r.headers["Location"]

    except requests.RequestException as e:
        traceback.print_exc()
        raise RuntimeError(f"Add XML to upload error: {e}")


def create_delivery(
    upload_url: str, bro_username: str, bro_password: str, project_number: str
) -> str:
    """Delivers the uploaded XML file, which is step 3 of 3 in the upload process."""

    upload_id = upload_url.split("/")[-1]
    payload = {"upload": int(upload_id)}

    deliver_url = (
        f"{settings.BRONHOUDERSPORTAAL_URL}/api/v2/{project_number}/leveringen"
    )

    try:
        r = requests.post(
            deliver_url,
            headers={"Content-type": "application/json"},
            data=json.dumps(payload),
            auth=(bro_username, bro_password),
        )
        r.raise_for_status()

        return r.headers["Location"]

    except requests.RequestException as e:
        traceback.print_exc()
        raise RuntimeError(f"Deliver uploaded XML error: {e}")


def check_delivery_status(
    delivery_url: str, bro_username: str, bro_password: str
) -> str:
    """Checks the Delivery info. Step 4 of 4 in the upload process."""
    try:
        r = requests.get(
            url=delivery_url,
            auth=(bro_username, bro_password),
        )

        return r

    except requests.RequestException as e:
        traceback.print_exc()
        raise RuntimeError(f"Delivery info check error: {e}")
