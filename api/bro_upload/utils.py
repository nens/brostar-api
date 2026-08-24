import csv
import datetime
import json
import logging
import zipfile
from io import BytesIO
from typing import Any

import defusedxml.ElementTree as DefusedET
import polars as pl
import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import api.models as api_models

logger = logging.getLogger("general")

retry_strategy = Retry(
    total=5,  # total number of retries
    backoff_factor=2,  # exponential backoff: 1s, 2s, 4s...
    status_forcelist=[429, 500, 501, 502, 503, 504],  # retry on these codes
    allowed_methods=["GET", "PATCH", "POST"],  # retry for POST as well (not default)
    raise_on_status=False,
)
adapter = HTTPAdapter(max_retries=retry_strategy)


def simplify_validation_errors(errors: list[str]) -> dict[str, str]:
    """Transforms the verbose pydantic errors to a readable format"""
    for err in errors:
        err["loc"] = [str(loc) for loc in err["loc"]]

    return {" - ".join(err["loc"]): err["msg"] for err in errors}


def detect_delimiter_from_content(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t"])
        return dialect.delimiter
    except (csv.Error, Exception):
        # Default fallback
        return ","


def read_csv(file: api_models.UploadFile | bytes) -> pl.DataFrame:
    if isinstance(file, bytes):
        sample = file[:2048].decode("utf-8", errors="ignore")
        delimiter = detect_delimiter_from_content(sample)
        return pl.read_csv(
            source=BytesIO(file),
            has_header=True,
            ignore_errors=False,
            truncate_ragged_lines=True,
            separator=delimiter,
        )

    # Handle FastAPI UploadFile or similar
    if hasattr(file, "file") and hasattr(file.file, "path"):
        with open(file.file.path, encoding="utf-8", errors="ignore") as f:
            sample = f.read(2048)
        delimiter = detect_delimiter_from_content(sample)
        return pl.read_csv(
            file.file.path,
            has_header=True,
            ignore_errors=False,
            truncate_ragged_lines=True,
            separator=delimiter,
        )

    # Handle normal path string
    if isinstance(file, str):
        with open(file, encoding="utf-8", errors="ignore") as f:
            sample = f.read(2048)
        delimiter = detect_delimiter_from_content(sample)
        return pl.read_csv(
            file,
            has_header=True,
            ignore_errors=False,
            truncate_ragged_lines=True,
            separator=delimiter,
        )

    raise TypeError("Unsupported file type passed to read_csv.")


def read_excel(file: api_models.UploadFile | bytes) -> pl.DataFrame:
    if isinstance(file, api_models.UploadFile):
        return pl.read_excel(
            source=file.file.path,
        )
    return pl.read_excel(
        source=file,
    )


def read_zip(file_instance: api_models.UploadFile) -> pl.DataFrame:
    csv_files = []
    xls_files = []
    xlsx_files = []
    with zipfile.ZipFile(file_instance.file) as z:
        for f in z.namelist():
            file_type = f.split(".")[-1]
            match file_type:
                case "csv":
                    csv_files.append(f)
                case "xls":
                    xls_files.append(f)
                case "xlsx":
                    xlsx_files.append(f)

        xlsx_files.extend(xls_files)
        excel_files = xlsx_files
        if not csv_files and not excel_files:
            raise ValueError("No CSV and no Excel files found in the zip archive.")

        # Read all CSV files into Polars DataFrames
        dfs = []
        for csv_file in csv_files:
            with z.open(csv_file) as file:
                file_bytes = file.read()  # Read the file as bytes
                dfs.append(read_csv(file_bytes))

        for excel in excel_files:
            with z.open(excel) as file:
                file_bytes = file.read()  # Read the file as bytes
                dfs.append(read_excel(file_bytes))

        # Combine all DataFrames into one, or return a list if separate DataFrames are desired
        return pl.concat(dfs)


def file_to_df(file_instance: api_models.UploadFile) -> pl.DataFrame:
    """Reads out csv or excel files and returns a pandas df."""
    filetype = file_instance.file.name.split(".")[-1].lower()
    if filetype == "csv":
        df = read_csv(file_instance)
    elif filetype in ["xls", "xlsx"]:
        df = read_excel(file_instance)
    elif filetype == "zip":
        df = read_zip(file_instance)
    else:
        raise ValueError(
            "Unsupported file type. Only CSV and Excel, or ZIP files are supported."
        )
    return df


def validate_xml_file(
    xml_file: str, bro_username: str, bro_password: str, project_number: str
) -> dict[str, Any]:
    """
    Validates a XML file with the Bronhouderportaal api.

    If invalid should return:
    - status
    - errors

    """
    url = f"{settings.BRONHOUDERSPORTAAL_URL}/api/v2/{project_number}/validatie"

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        r = session.post(
            url=url,
            data=xml_file,
            headers={"Content-Type": "application/xml"},
            auth=(bro_username, bro_password),
            timeout=300,  # Update as Replace GMN_StartRegistration runs out of time.
        )
        r.raise_for_status()
        return r.json()

    except requests.exceptions.HTTPError as e:
        status = "NIET-VALIDE"
        match r.status_code:
            case 401:
                return {
                    "status": status,
                    "errors": [
                        f"Het gebruikte token is niet gemachtigd voor project {project_number}"
                    ],
                }
            case 403:
                return {
                    "status": status,
                    "errors": [
                        f"Het gebruikte token heeft niet de juiste rechten voor project {project_number}"
                    ],
                }
            case 500 | 502 | 503 | 504:
                return {
                    "status": status,
                    "errors": [
                        "De BRO API is momenteel niet beschikbaar. Neem contact op met servicedesk@nelen-schuurmans.nl"
                    ],
                }
            case _:
                return {
                    "status": status,
                    "errors": [
                        f"Er is een fout opgetreden bij het valideren van het XML bestand: {e}"
                    ],
                }

    except Exception as e:
        logger.info(e)
        return {
            "status": "NIET-VALIDE",
            "errors": [
                f"Er is een fout opgetreden bij het valideren van het XML bestand: {e}"
            ],
        }


def create_upload_url(
    bro_username: str, bro_password: str, project_number: str
) -> dict[str, str]:
    """
    POST to the BRO api to receive an upload id, which is step 1 of 3 in the upload process.

    Return:
    - status
    - upload_url (if status is OK)
    """
    url = f"{settings.BRONHOUDERSPORTAAL_URL}/api/v2/{project_number}/uploads"

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        r = session.post(
            url,
            headers={"Content-Type": "application/xml"},
            auth=(bro_username, bro_password),
            timeout=60,
        )
        r.raise_for_status()
        upload_url = r.headers["Location"]

        return {"status": "OK", "upload_url": upload_url}

    except requests.HTTPError as e:
        logger.info(e)
        match r.status_code:
            case 401:
                return {
                    "status": "NIET-VALIDE",
                    "errors": [
                        f"Het gebruikte token is niet gemachtigd voor project {project_number}"
                    ],
                }
            case _:
                return {"status": "NIET-VALIDE", "errors": [f"Error: {e}."]}

    except Exception as e:
        logger.info(e)
        return {
            "status": "NIET-VALIDE",
            "errors": [
                f"Er is een fout opgetreden bij het aanmaken van de upload: {e}."
            ],
        }


def add_xml_to_upload(
    xml_file: str,
    upload_url: str,
    bro_username: str,
    bro_password: str,
) -> str:
    """Add the XML to the upload request, which is step 2 of 3 in the upload process."""
    datetime_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    upload_url = f"{upload_url}/brondocumenten"

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        r = session.post(
            upload_url,
            headers={"Content-Type": "application/xml"},
            auth=(bro_username, bro_password),
            data=xml_file,
            params={"filename": f"{datetime_str}_BROSTAR_request.xml"},
            timeout=60,
        )
        r.raise_for_status()
        return r.headers["Location"]

    except requests.RequestException as e:
        logger.info(e)
        return None


def create_delivery(
    upload_url: str, bro_username: str, bro_password: str, project_number: str
) -> str:
    """Delivers the uploaded XML file, which is step 3 of 3 in the upload process."""

    upload_id = upload_url.split("/")[-1]
    payload = {"upload": int(upload_id)}

    deliver_url = (
        f"{settings.BRONHOUDERSPORTAAL_URL}/api/v2/{project_number}/leveringen"
    )

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        r = session.post(
            deliver_url,
            headers={"Content-type": "application/json"},
            data=json.dumps(payload),
            auth=(bro_username, bro_password),
            timeout=60,
        )
        r.raise_for_status()

        return r.headers["Location"]

    except requests.RequestException as e:
        logger.info(e)
        return None


def check_delivery_status(
    delivery_url: str, bro_username: str, bro_password: str
) -> dict[str, Any]:
    """Checks the Delivery info. Step 4 of 4 in the upload process."""

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        r = session.get(
            url=delivery_url,
            auth=(bro_username, bro_password),
            timeout=20,
        )

        return r.json()

    except requests.RequestException as e:
        logger.info(e)
        return None


_ROOT_TAG_TO_REQUEST_TYPE: dict[str, str] = {
    "registrationRequest": "registration",
    "replaceRequest": "replace",
    "insertRequest": "insert",
    "moveRequest": "move",
    "deleteRequest": "delete",
}


def parse_raw_xml_metadata(xml_bytes: bytes) -> dict[str, str]:
    """Safely parse a BRO XML file and extract request_type, registration_type, and bro_domain.

    Uses defusedxml to prevent XXE attacks. Only reads the root element and the
    first child of <sourceDocument> — no deeper parsing.

    Raises:
        ValueError: if the XML cannot be parsed or the expected structure is missing.
    """
    try:
        root = DefusedET.fromstring(xml_bytes)
    except Exception as e:
        raise ValueError(f"XML parse error: {e}") from e

    local_root = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    request_type = _ROOT_TAG_TO_REQUEST_TYPE.get(local_root)
    if request_type is None:
        raise ValueError(f"Unrecognised root element: {local_root!r}")

    # Find <sourceDocument> (may have a namespace prefix)
    source_doc = None
    for child in root:
        local_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local_tag == "sourceDocument":
            source_doc = child
            break

    if source_doc is None:
        raise ValueError("No <sourceDocument> element found")

    first_child = next(iter(source_doc), None)
    if first_child is None:
        raise ValueError("<sourceDocument> has no children")

    local_child = (
        first_child.tag.split("}")[-1] if "}" in first_child.tag else first_child.tag
    )
    registration_type = local_child
    bro_domain = (
        registration_type.split("_")[0]
        if "_" in registration_type
        else registration_type
    )

    return {
        "request_type": request_type,
        "registration_type": registration_type,
        "bro_domain": bro_domain,
    }


def include_delivery_responsible_party(
    delivery_responsible_party: str, data_owner: str
) -> bool:
    """Check if delivery_responsible_party is equal to data_owner.kvk

    If not, than the delivery responsible party should be included in the document.
    """
    if not data_owner:
        return True

    if not delivery_responsible_party:
        return False

    org = api_models.Organisation.objects.get(uuid=data_owner)
    return org.kvk_number != delivery_responsible_party
