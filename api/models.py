import uuid

from django.contrib.auth.models import User
from django.db.models import JSONField
from encrypted_model_fields.fields import EncryptedCharField

from . import choices
from django.db import models


class Organisation(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    kvk_number = models.CharField(max_length=8)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    bro_user_token = EncryptedCharField(max_length=100)
    bro_user_password = EncryptedCharField(max_length=100)
    project_number = models.CharField(max_length=20)

    def __str__(self):
        return self.user.username
    



class ImportTask(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bro_domain = models.CharField(
        max_length=3, choices=choices.BRO_DOMAIN_CHOICES, default=None
    )
    organisation = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20, choices=choices.STATUS_CHOICES, default="PENDING", blank=True
    )
    log = models.TextField(blank=True)

    def __str__(self):
        return f"{self.bro_domain} import - {self.organisation} ({self.created_at})"


class UploadTask(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    bro_domain = models.CharField(
        max_length=3, choices=choices.BRO_DOMAIN_CHOICES, default=None
    )
    registration_type = models.CharField(
        blank=False, max_length=235, choices=choices.REGISTRATION_TYPE_OPTIONS
    )
    request_type = models.CharField(
        blank=False, max_length=235, choices=choices.REQUEST_TYPE_OPTIONS
    )
    metadata = JSONField("Metadata", default=dict, blank=False)
    sourcedocument_data = JSONField("Sourcedocument data", default=dict, blank=False)
    status = models.CharField(max_length=500, blank=True, null=True)
    log = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.request_type} {self.registration_type} {self.created}"
