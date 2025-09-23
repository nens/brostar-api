import datetime
import json
import logging
import zipfile
from typing import Any, TypeVar

import polars as pl
import requests
from django.conf import settings

import api.models as api_models

logger = logging.getLogger("general")

T = TypeVar("T", bound="api_models.UploadFile")


def simplify_validation_errors(errors: list[str]) -> dict[str, str]:
    """Transforms the verbose pydantic errors to a readable format"""
    return {" - ".join(err["loc"]): err["msg"] for err in errors}


def read_csv(file: T | bytes) -> pl.DataFrame:
    if isinstance(file, api_models.UploadFile):
        return pl.read_csv(
            file.file.path,
            has_header=True,
            ignore_errors=False,
            truncate_ragged_lines=True,
        )
    return pl.read_csv(
        source=file,
        has_header=True,
        ignore_errors=False,
        truncate_ragged_lines=True,
    )


def read_excel(file: T | bytes) -> pl.DataFrame:
    if isinstance(file, api_models.UploadFile):
        return pl.read_excel(
            source=file.file.path,
        )
    return pl.read_excel(
        source=file,
    )


def read_zip(file_instance: T) -> pl.DataFrame:
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


def file_to_df(file_instance: T) -> pl.DataFrame:
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

    try:
        r = requests.post(
            url=url,
            data=xml_file,
            headers={"Content-Type": "application/xml"},
            auth=(bro_username, bro_password),
            timeout=60,
        )
        r.raise_for_status()
        return r.json()

    except Exception as e:
        status = "NIET-VALIDE"
        if r.status_code == 401:
            return {
                "status": status,
                "errors": f"Het gebruikte token is niet gemachtigd voor project {project_number}",
            }
        elif r.status_code == 403:
            return {
                "status": status,
                "errors": f"Het gebruikte token heeft niet de juiste rechten voor project {project_number}",
            }
        elif r.status_code > 499:
            return {
                "status": status,
                "errors": "De BRO API is momenteel niet beschikbaar. Neem contact op met servicedesk@nelen-schuurmans.nl",
            }
        else:
            return {
                "status": status,
                "errors": f"Er is een fout opgetreden bij het valideren van het XML bestand: {e}",
            }


def create_upload_url(bro_username: str, bro_password: str, project_number: str) -> str:
    """POST to the BRO api to receive an upload id, which is step 1 of 3 in the upload process."""
    url = f"{settings.BRONHOUDERSPORTAAL_URL}/api/v2/{project_number}/uploads"

    try:
        r = requests.post(
            url,
            headers={"Content-Type": "application/xml"},
            auth=(bro_username, bro_password),
            timeout=60,
        )
        r.raise_for_status()
        upload_url = r.headers["Location"]

        return upload_url

    except requests.RequestException as e:
        logger.exception(e)
        raise RuntimeError(f"Create upload url error: {e}")


def add_xml_to_upload(
    xml_file: str,
    upload_url: str,
    bro_username: str,
    bro_password: str,
) -> str:
    """Add the XML to the upload request, which is step 2 of 3 in the upload process."""
    datetime_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    upload_url = f"{upload_url}/brondocumenten"

    try:
        r = requests.post(
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
        logger.exception(e)
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
            timeout=60,
        )
        r.raise_for_status()

        return r.headers["Location"]

    except requests.RequestException as e:
        logger.exception(e)
        raise RuntimeError(f"Deliver uploaded XML error: {e}")


def check_delivery_status(
    delivery_url: str, bro_username: str, bro_password: str
) -> dict[str, Any]:
    """Checks the Delivery info. Step 4 of 4 in the upload process."""
    try:
        r = requests.get(
            url=delivery_url,
            auth=(bro_username, bro_password),
            timeout=20,
        )

        return r.json()

    except requests.RequestException as e:
        logger.exception(e)
        raise RuntimeError(f"Delivery info check error: {e}")


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
