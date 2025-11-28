import logging

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from . import tasks
from .models import ImportTask, InviteUser, UploadTask, UserProfile
from .utils import create_objects

logger = logging.getLogger(__name__)


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

    if instance.registration_type in ["GMW_Shortening", "GMW_Lengthening"]:
        for tube in instance.sourcedocument_data.get("monitoringTubes", []):
            plain_tube_length = get_plain_tube_part_length(
                instance.metadata.get("broId"),
                tube.get("tubeNumber"),
                tube.get("tubeTopPosition"),
            )
            if plain_tube_length is not None:
                tube["plainTubePartLength"] = str(plain_tube_length)

    if (
        "gebeurtenis mag niet voor de laatst geregistreerde gebeurtenis"
        in instance.bro_errors
    ):
        instance.request_type = "insert"
        instance.metadata.update({"correctionReason": "eigenCorrectie"})
        instance.bro_errors = ""
        instance.status = "PENDING"


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
        if len(features) > 0:
            gm_gmw_pk = features[0].get("properties", {}).get("pk")
        else:
            gm_gmw_pk = None

        if gm_gmw_pk:
            r = requests.get(
                f"https://api.pdok.nl/bzk/bro-gminsamenhang-karakteristieken/ogc/v1/collections/gm_gmw_monitoringtube/items?f=json&gm_gmw_fk={gm_gmw_pk}&tube_number={tube_number}",
                timeout=5,
            )
            if r.status_code < 300:
                return round(
                    float(tube_top_position)
                    - float(
                        r.json()
                        .get("features", [])[0]
                        .get("properties", {})
                        .get("screen_top_position")
                    ),
                    3,
                )

    return None


@receiver(post_save, sender=UploadTask)
def post_save_upload_task(sender, instance: UploadTask, created, **kwargs):
    """Handle registration where it should be an insert."""
    if instance.status == "PENDING" and instance.data_owner:
        instance._skip_signal = True
        instance.status = "PROCESSING"
        instance.progress = 5
        instance.log = "Starting task."
        instance.save()

        # Accessing the authenticated user's username and token
        username = instance.data_owner.bro_user_token
        password = instance.data_owner.bro_user_password

        # Start the celery task
        tasks.upload_task(instance.uuid, username, password)

    if (
        instance.status == "COMPLETED"
        and instance.request_type == "registration"
        and instance.data_owner
    ):
        create_objects(
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
        # Start the celery task
        tasks.import_bro_data_task.delay(instance.uuid)
