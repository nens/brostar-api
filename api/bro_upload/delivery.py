import logging
import time
from typing import Any

from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string

from .. import models as api_models
from . import utils

logger = logging.getLogger(__name__)


class XMLGenerationError(Exception):
    """Exception raised when XML generation fails."""

    pass


class XMLValidationError(Exception):
    """Exception raised when XML validation fails."""

    pass


class DeliveryError(Exception):
    """Exception raised when the delivery has an error."""

    pass


class BRODelivery:
    """Handles the complete process of uploading data to the BRO.

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

    def __init__(
        self,
        upload_task_instance: api_models.UploadTask,
        bro_username: str,
        bro_password: str,
    ) -> None:
        self.upload_task_instance = upload_task_instance
        self.bro_username = bro_username
        self.bro_password = bro_password

    def process(self) -> None:
        # Generate the XML file.
        xml_file = self._generate_xml_file()

        # Validate with the BRO API
        self._validate_xml_file(xml_file)

        # Deliver the XML file. The deliver_url is returned to use for the check.
        deliver_url = self._deliver_xml_file(xml_file)

        # Check of the status of the delivery. Retries 3 times before failing
        retries_count = 0

        while retries_count < 4:
            if self._check_delivery(deliver_url):
                return
            else:
                time.sleep(10)
                retries_count += 1

        raise DeliveryError("Delivery was unsuccesfull")

    def _generate_xml_file(self) -> str:
        try:
            generator = XMLGenerator(
                self.upload_task_instance.registration_type,
                self.upload_task_instance.request_type,
                self.upload_task_instance.metadata,
                self.upload_task_instance.sourcedocument_data,
            )
            return generator.create_xml_file()

        except Exception as e:
            logger.exception(e)
            raise RuntimeError(f"Error generating XML file: {e}") from e

    def _validate_xml_file(self, xml_file: str) -> None:
        validation_response = utils.validate_xml_file(
            xml_file,
            self.bro_username,
            self.bro_password,
            self.upload_task_instance.project_number,
        )

        if validation_response["status"] != "VALIDE":
            raise XMLValidationError(
                f"Errors while validating the XML file: {validation_response['errors']}"
            )
        else:
            return

    def _deliver_xml_file(self, xml_file: str) -> str:
        """The upload consists of 4 steps:
        1) Requesting an upload by posting to the BRO api. Returns an upload_url
        2) Adding the XML file to the upload
        3) The actual delivery
        """

        upload_url = utils.create_upload_url(
            self.bro_username,
            self.bro_password,
            self.upload_task_instance.project_number,
        )
        utils.add_xml_to_upload(
            xml_file,
            upload_url,
            self.bro_username,
            self.bro_password,
        )
        delivery_url = utils.create_delivery(
            upload_url,
            self.bro_username,
            self.bro_password,
            self.upload_task_instance.project_number,
        )

        return delivery_url

    def _check_delivery(self, delivery_url: str) -> bool:
        """Checks the delivery status."""

        delivery_info = utils.check_delivery_status(
            delivery_url, self.bro_username, self.bro_password
        )

        errors = delivery_info["brondocuments"][0]["errors"]

        if errors:
            raise DeliveryError(f"Errors found after delivering the XML file: {errors}")

        else:
            delivery_status = delivery_info["status"]
            delivery_brondocument_status = delivery_info["brondocuments"][0][
                "status"
            ]

            if (
                delivery_status == "DOORGELEVERD"
                and delivery_brondocument_status == "OPGENOMEN_LVBRO"
            ):
                return True

            else:
                return False


class XMLGenerator:
    """XML generator based on Django Templates."""

    def __init__(
        self,
        registration_type: str,
        request_type: str,
        metadata: dict[str, Any],
        sourcedocs_data: dict[str, Any],
    ) -> None:
        self.metadata = metadata
        self.sourcedocs_data = sourcedocs_data
        self.template_filepath = f"{request_type}_{registration_type}.html"

    def create_xml_file(self) -> str:
        """Fills in the provided data into the templates"""
        try:
            rendered_xml = render_to_string(
                self.template_filepath,
                {
                    "metadata": self.metadata,
                    "sourcedocs_data": self.sourcedocs_data,
                },
            )
            return rendered_xml

        except TemplateDoesNotExist as e:
            logger.exception(e)
            raise XMLGenerationError(
                "De aangeleverde combinatie van request type en registratie type is niet mogelijk. Als de combinatie in de BRO wel mogelijk is, vraag dan deze combinatie aan bij Nelen & Schuurmans."
            ) from e

        except Exception as e:
            logger.exception(e)
            raise XMLGenerationError(e) from e
