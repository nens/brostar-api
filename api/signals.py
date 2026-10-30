import logging
import os
import re

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from . import tasks
from .models import ImportTask, InviteUser, UploadTask, UserProfile
from .utils import create_objects, delete_objects, update_objects

logger = logging.getLogger(__name__)


# Error translation registry with regex patterns for extracting dynamic values
BRO_ERROR_TRANSLATIONS = {
    # Static error patterns (exact match)
    "static": {
        "FormationResistanceDetermination.determinationType) moet aanwezig zijn": "De meetconfiguraties voor dit Formatieweerstandsdossier zijn nog niet aangeleverd. Lever eerst de meetconfiguraties aan."
    },
    # Dynamic error patterns with regex extraction
    "dynamic": [
        {
            "pattern": r"De combinatie van Posities inmeten\.naam gebeurtenis \(PositionsMeasuring\.eventName\) = (.+?) op Posities inmeten\.datum gebeurtenis \(PositionsMeasuring\.eventDate\) = \((\d{4}-\d{2}-\d{2}), JJJJ-MM-DD\) is niet correct: Er is reeds een zelfde gebeurtenis op deze datum geregistreerd\.",
            "template": "Er is al een {eventName} geregistreerd op {eventDate}.",
            "groups": {"eventName": 1, "eventDate": 2},
        }
    ],
}


def translate_bro_error(error_message: str) -> str:
    """
    Translate BRO error messages to user-friendly Dutch messages.

    Supports both static exact matches and dynamic patterns with value extraction.

    Args:
        error_message: The original BRO error message

    Returns:
        Translated error message or original if no translation found
    """
    if not error_message:
        return error_message

    # Check static translations first
    for static_error, translation in BRO_ERROR_TRANSLATIONS.get("static", {}).items():
        if static_error in error_message:
            return translation

    # Check dynamic translations
    for dynamic_pattern in BRO_ERROR_TRANSLATIONS.get("dynamic", []):
        match = re.search(dynamic_pattern["pattern"], error_message)
        if match:
            template = dynamic_pattern["template"]
            groups = dynamic_pattern["groups"]

            # Extract values and format template
            format_dict = {}
            for var_name, group_index in groups.items():
                format_dict[var_name] = match.group(group_index)

            return template.format(**format_dict)

    return error_message


@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created, **kwargs):
    """After a user accepts a nens auth client invitation, this creates a UserProfile.
    The organisation initially set in the InviteUser is copied to the UserProfile.
    """
    try:
        invite_user = InviteUser.objects.get(email=instance.email)
        organisation = invite_user.organisation
    except InviteUser.DoesNotExist:
        organisation = None

    if created:
        UserProfile.objects.create(user=instance, organisation=organisation)
    else:
        user_profile = UserProfile.objects.get(user=instance)
        if not user_profile.organisation:
            user_profile.organisation = organisation
            user_profile.save()


@receiver(pre_save, sender=UploadTask)
def pre_save_upload_task(sender, instance: UploadTask, **kwargs):
    """Handle registration where it should be an insert."""
    if not isinstance(instance.bro_errors, str):
        instance.bro_errors = str(instance.bro_errors)

    # Raw XML uploads bypass template logic; do not apply any auto-corrections.
    if instance.metadata.get("_is_raw_xml"):
        return

    is_staging = "staging" in os.getenv("NENS_AUTH_RESOURCE_SERVER_ID", "")

    if instance.registration_type in ["GMW_Shortening", "GMW_Lengthening"]:
        for tube in instance.sourcedocument_data.get("monitoringTubes", []):
            plain_tube_length = get_plain_tube_part_length(
                instance.metadata.get("broId"),
                tube.get("tubeNumber"),
                tube.get("tubeTopPosition"),
            )
            if plain_tube_length is not None and not is_staging:
                tube["plainTubePartLength"] = str(plain_tube_length)

    if any(
        err in instance.bro_errors
        for err in [
            "gebeurtenis mag niet voor de laatst geregistreerde gebeurtenis",
            "moet liggen na de waarde van het attribuut",
        ]
    ):
        instance.request_type = "insert"
        instance.metadata.update({"correctionReason": "eigenCorrectie"})
        instance.bro_errors = ""
        instance.status = "PENDING"

    # Translate BRO error messages to user-friendly format
    instance.bro_errors = translate_bro_error(instance.bro_errors)


def get_plain_tube_part_length(
    bro_id: str, tube_number: int, tube_top_position: float
) -> float | None:
    """Fetch the plain tube part length for a given bro_id and tube_number."""
    import requests

    r = requests.get(
        f"https://api.pdok.nl/bzk/bro-gminsamenhang-karakteristieken/ogc/v1/collections/gm_gmw/items?f=json&bro_id={bro_id}",
        timeout=5,
    )
    if r.status_code < 300:
        features = r.json().get("features", [])
        logger.info(f"Fetched features for bro_id {bro_id}: {features}")
        if len(features) > 0:
            gm_gmw_pk = features[0].get("properties", {}).get("gm_gmw_pk")
        else:
            gm_gmw_pk = None

        if gm_gmw_pk:
            r = requests.get(
                f"https://api.pdok.nl/bzk/bro-gminsamenhang-karakteristieken/ogc/v1/collections/gm_gmw_monitoringtube/items?f=json&gm_gmw_fk={gm_gmw_pk}&tube_number={tube_number}",
                timeout=5,
            )
            if r.status_code < 300:
                features = r.json().get("features", [])
                if len(features) == 0:
                    return None

                return round(
                    float(tube_top_position)
                    - float(
                        features[0].get("properties", {}).get("screen_top_position")
                    ),
                    3,
                )

    return None


# def poll_bro_relations(bro_id: str) -> list[str]:
#     """
#     Function to find all related bro-id's based on a GMW-BRO-ID

#     :param bro_id: Description
#     :type bro_id: str
#     :return: Description
#     :rtype: list[str]
#     """
#     if not is_valid_bro_id(bro_id):
#         return []

#     s = request.Session()
#     r = s.get(f"{settings.PUBLIEKE_BRO_URL}/gm/v1/gmw-relations?{bro_id}", timeout=20)
#     r.raise_for_status()

#     relations = r.json()

#     return ...

# FINALIZE_MAPPING = {
#     "GLD": None, # Do not need sourcedocument data
#     "GMN": GMNClosure,
#     "FRD": None, # Do not need sourcedocument data
# }

# def finalize_relation(relation: str, event_date: str, data_owner: str) -> None:
#     metadata = UploadTaskMetadata(
#         ""
#     )
#     sourcedocument_data = ""
#     UploadTask.objects.create(
#         project_number = "",
#         data_owner=data_owner,
#         metadata=metadata,
#         sourcedocument_data=sourcedocument_data,
#     )
#     return


def close_related_objects(bro_id: str, event_date: str, data_owner: str) -> None:
    """
    Create UploadTasks for all related (GMN, GLD, FRD) domains.
    For GLD, no date is needed.
    For GMN, the removal date should be used.
    For FRD, no date is needed.
    """
    return
    # relations = poll_bro_relations(bro_id)

    # for relation in relations:
    #     finalize_relation(relation, event_date, data_owner)


@receiver(post_save, sender=UploadTask)
def post_save_upload_task(sender, instance: UploadTask, created, **kwargs):
    """Handle registration where it should be an insert."""
    # Raw XML uploads manage their own Celery dispatch; skip the standard signal chain.
    if instance.metadata.get("_is_raw_xml"):
        return

    if instance.status == "PENDING" and instance.data_owner:
        instance._skip_signal = True
        instance.status = "PROCESSING"
        instance.progress = 5
        instance.log = "Starting task."
        instance.save()

        # Start the celery task
        tasks.upload_task(instance.uuid)

    if (
        instance.status == "COMPLETED"
        and instance.request_type in ["registration", "insert"]
        and instance.data_owner
    ):
        # If a GMW_Removal was completed succesfully, we also might have to send
        # a GMN_MeasuringPointEndDate, GLD_Closure and a FRD_Closure
        # To achieve this, the gmw_relations should be polled
        # Dependent on this, all relations should be closed
        if instance.registration_type == "GMW_Removal":
            close_related_objects(
                instance.bro_id,
                instance.sourcedocument_data.get("eventDate", "1899-01-01"),
                instance.data_owner,
            )

        # Create DB objects to show to users.
        create_objects(
            instance.registration_type,
            instance.bro_id,
            instance.metadata,
            instance.sourcedocument_data,
            instance.data_owner,
        )
    elif (
        instance.status == "COMPLETED"
        and instance.request_type in ["replace", "move"]
        and instance.data_owner
    ):
        update_objects(
            instance.registration_type,
            instance.bro_id,
            instance.metadata,
            instance.sourcedocument_data,
            instance.data_owner,
        )
    elif (
        instance.status == "COMPLETED"
        and instance.request_type == "delete"
        and instance.data_owner
    ):
        delete_objects(
            instance.registration_type,
            instance.bro_id,
            instance.metadata,
            instance.sourcedocument_data,
            instance.data_owner,
        )


@receiver(post_save, sender=ImportTask)
def post_save_import_task(sender, instance: ImportTask, created, **kwargs):
    """Handle registration where it should be an insert."""
    if instance.status == "PENDING":
        # Use the chord-based fan-out task for non-blocking parallel imports.
        # The original import_bro_data_task is kept for backward compatibility.
        tasks.fetch_bro_ids_and_dispatch_task.delay(instance.uuid)
