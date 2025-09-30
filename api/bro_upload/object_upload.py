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
            logger.warning(e)
            raise XMLGenerationError(
                "De aangeleverde combinatie van request type en registratie type is niet mogelijk. Als de combinatie in de BRO wel mogelijk is, vraag dan deze combinatie aan bij Nelen & Schuurmans."
            ) from e

        except Exception as e:
            logger.warning(e)
            raise XMLGenerationError(e) from e
