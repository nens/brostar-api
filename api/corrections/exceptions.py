from rest_framework import status
from rest_framework.exceptions import APIException


class BROUnavailable(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "De publieke BRO-uitgifteservice is niet bereikbaar."
    default_code = "bro_unavailable"


class ObjectNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Het opgevraagde BRO-object is niet gevonden."
    default_code = "object_not_found"


class ObservationNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "De opgevraagde observatie is niet gevonden."
    default_code = "observation_not_found"

    def __init__(self, bro_id: str, observation_id: str) -> None:
        super().__init__(
            f"observation_id '{observation_id}' is niet bekend binnen {bro_id}."
        )


class CorrectionValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "De correctie kan niet worden uitgevoerd."
    default_code = "correction_invalid"
