import logging
import time
from typing import Any

import requests
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string

from api.bro_import import bulk_import, config

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
        upload_task_instance_uuid: str,
        bro_username: str,
        bro_password: str,
    ) -> None:
        # Lookup and update upload task instance
        self.upload_task_instance: api_models.UploadTask = (
            api_models.UploadTask.objects.get(uuid=upload_task_instance_uuid)
        )
        self.upload_task_instance.status = "PROCESSING"
        self.upload_task_instance.save()

        self.bro_username: str = bro_username
        self.bro_password: str = bro_password
        self.bro_id: str = ""

    def process(self) -> None:
        # Generate the XML file.
        try:
            xml_file = self._generate_xml_file()
            print(xml_file)
            self.upload_task_instance.progress = 25.00
            self.upload_task_instance.save()
        except Exception as e:
            self.upload_task_instance.log = e
            self.upload_task_instance.status = "FAILED"
            self.upload_task_instance.save()
            return

        # Validate with the BRO API
        try:
            self._validate_xml_file(xml_file)
            self.upload_task_instance.progress = 50.00
            self.upload_task_instance.save()
        except Exception as e:
            self.upload_task_instance.log = e
            self.upload_task_instance.status = "FAILED"
            self.upload_task_instance.save()
            return

        # Deliver the XML file. The deliver_url is returned to use for the check.
        try:
            deliver_url = self._deliver_xml_file(xml_file)
            self.upload_task_instance.bro_delivery_url = deliver_url
            self.upload_task_instance.progress = 75.00
            self.upload_task_instance.save()
        except Exception as e:
            self.upload_task_instance.log = e
            self.upload_task_instance.status = "FAILED"
            self.upload_task_instance.save()
            return

        # Check of the status of the delivery. Retries 3 times before failing
        retries_count = 0

        while retries_count < 4:
            if self._check_delivery(deliver_url):
                # Update upload task instance
                self.upload_task_instance.bro_id = self.bro_id
                self.upload_task_instance.progress = 100.0
                self.upload_task_instance.status = "COMPLETED"
                self.upload_task_instance.log = "The upload was done successfully"
                self.upload_task_instance.save()

                try:
                    # Add 1 to the organisations request count
                    organisation = api_models.Organisation.objects.get(
                        uuid=self.upload_task_instance.data_owner.uuid
                    )
                    organisation.request_count += 1
                    organisation.save()
                except Exception as e:
                    self.upload_task_instance.log = (
                        f"The upload was done successfully. BUT: {e}"
                    )
                    self.upload_task_instance.save()

                # After the upload was done succesfully, the data should be imported into the API
                try:
                    object_importer_class = config.object_importer_mapping[
                        self.upload_task_instance.bro_domain
                    ]
                    importer = object_importer_class(
                        bro_id=self.upload_task_instance.bro_id,
                        data_owner=self.upload_task_instance.data_owner,
                    )
                    importer.run()

                    return

                except requests.RequestException as e:
                    logger.exception(e)
                    raise bulk_import.DataImportError(
                        f"Error while importing data for bro id: {self.bro_id}: {e}"
                    ) from e
            else:
                time.sleep(10)
                retries_count += 1

        self.upload_task_instance.status = "UNFINISHED"
        self.upload_task_instance.log = "After 4 times checking, the delivery status in the BRO was still not 'DOORGELEVERD'. Please checks its status manually."
        self.upload_task_instance.save()

        return

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
            self.upload_task_instance.bro_errors = validation_response["errors"]
            self.upload_task_instance.save()
            raise XMLValidationError("Errors while validating the XML file")
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
            delivery_brondocument_status = delivery_info["brondocuments"][0]["status"]

            if (
                delivery_status == "DOORGELEVERD"
                and delivery_brondocument_status == "OPGENOMEN_LVBRO"
            ):
                # Set BRO id to self to enable an import task based on the bro id. This keeps the data up2date in the api.
                self.bro_id = delivery_info["brondocuments"][0]["broId"]

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
