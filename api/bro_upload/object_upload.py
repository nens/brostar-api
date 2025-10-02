import logging
from typing import Any

from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string

logger = logging.getLogger("general")


class XMLGenerationError(Exception):
    """Exception raised when XML generation fails."""

    pass


class XMLValidationError(Exception):
    """Exception raised when XML validation fails."""

    pass


class DeliveryError(Exception):
    """Exception raised when the delivery has an error."""

    pass


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
        self.status = "PENDING"
        self.error_message = ""

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
            self.status = "COMPLETED"
            return rendered_xml

        except TemplateDoesNotExist as e:
            logger.info(f"Template does not exist: {e}")
            self.status = "FAILED"
            self.error_message = (
                f"Template for {self.template_filepath.strip('.html')} does not exist."
            )
            return ""

        except Exception as e:
            logger.info(f"Failed during XML generation: {e}")
            self.status = "FAILED"
            self.error_message = f"Failed during XML generation: {e}"
            return ""
