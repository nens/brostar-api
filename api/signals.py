from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from nens_auth_client.models import Invitation

from .models import InviteUser, UserProfile


@receiver(post_save, sender=InviteUser)
def create_invitation(sender, instance, created, **kwargs):
    """Create an nens auth client Invitation when an InviteUser is created."""
    if created:
        invitation = Invitation.objects.create(email=instance.email)
        instance.nens_auth_client_invitation = invitation
        instance.save()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created, **kwargs):
    """After a user accepts a nens auth client invitation, this creates a UserProfile.
    The organisation initially set in the InviteUser is copied to the UserProfile.
    """
    try:
        print(instance.email)
        invite_user = InviteUser.objects.get(email=instance.email)
        UserProfile.objects.update_or_create(
            user=instance, organisation=invite_user.organisation
        )
    except InviteUser.DoesNotExist:
        UserProfile.objects.create(user=instance)
