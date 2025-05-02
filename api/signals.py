from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from . import tasks
from .models import ImportTask, InviteUser, UploadTask, UserProfile


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
    if (
        "gebeurtenis mag niet voor de laatst geregistreerde gebeurtenis"
        in instance.bro_errors
    ):
        instance.request_type = "insert"
        instance.metadata.update({"correctionReason": "eigenCorrectie"})
        instance.bro_errors = ""
        instance.status = "PENDING"


@receiver(post_save, sender=UploadTask)
def post_save_upload_task(sender, instance: UploadTask, created, **kwargs):
    """Handle registration where it should be an insert."""
    if instance.status == "PENDING" and instance.data_owner:
        # Accessing the authenticated user's username and token
        username = instance.data_owner.bro_user_token
        password = instance.data_owner.bro_user_password

        # Start the celery task
        tasks.upload_task(instance.uuid, username, password)


@receiver(post_save, sender=ImportTask)
def post_save_import_task(sender, instance: ImportTask, created, **kwargs):
    """Handle registration where it should be an insert."""
    if instance.status == "PENDING":
        # Start the celery task
        tasks.import_bro_data_task.delay(instance.uuid)
