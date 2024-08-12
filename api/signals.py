from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import InviteUser, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created, **kwargs):
    """After a user accepts a nens auth client invitation, this creates a UserProfile.
    The organisation initially set in the InviteUser is copied to the UserProfile.
    """
    if created:
        try:
            UserProfile.objects.create(
                user=instance,
            )

        except InviteUser.DoesNotExist:
            UserProfile.objects.create(user=instance)

    else:
        try:
            invite_user = InviteUser.objects.get(email=instance.email)
            user_profile = UserProfile.objects.get(user=instance)
            user_profile.organisation = invite_user.organisation
            user_profile.save()

        except InviteUser.DoesNotExist:
            pass
