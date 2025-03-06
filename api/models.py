import uuid
from datetime import date
from typing import Any

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import JSONField, Q, UniqueConstraint
from encrypted_model_fields.fields import EncryptedCharField
from nens_auth_client.models import Invitation
from rest_framework_api_key.models import AbstractAPIKey

from api import choices, tasks


class PersonalAPIKey(AbstractAPIKey):
    """Personal API Key class

    id: {key}.{prefix} primary key
    prefix: for key lookups, unique, max_lenght=8
    hashed_key: max_lenght=100
    created: datetime
    name: description of this key's usage
    revoked: boolean
    expiry_date: datetime
    is_password: for migrating username/password combinations, boolean
    user: foreign key to user
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")

    scope = models.TextField(
        help_text="A space-separated list of {endpoint|*}:{read|readwrite}.",
        default="*:readwrite",
    )

    is_password = models.BooleanField(
        help_text="Whether this key was migrated from a former password.",
        default=False,
    )

    # Monitor the usage of the key
    last_used = models.DateField(
        help_text="Last time the API key was used.",
        default=None,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Personal API Key"
        verbose_name_plural = "Personal API Keys"

        constraints = [
            # Every user has at most 1 key with is_password=True
            UniqueConstraint(
                fields=["user"],
                condition=Q(is_password=True),
                name="unique_password_user",
            ),
        ]

    def update_last_used(self):
        """Update the last time the API key has been used,
        don't override if that day is today.
        """
        today = date.today()
        if self.last_used != today:
            self.last_used = today
            super().save(update_fields=["last_used"])


class Organisation(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    kvk_number = models.CharField(max_length=8)
    bro_user_token = EncryptedCharField(max_length=100, blank=True, null=True)
    bro_user_password = EncryptedCharField(max_length=100, blank=True, null=True)
    request_count = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Contract(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.OneToOneField(
        Organisation, on_delete=models.CASCADE, null=False
    )
    start_date = models.DateTimeField(null=False, blank=False)
    end_date = models.DateTimeField()
    nr_of_messages = models.BigIntegerField(null=False, blank=False, default=0)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.organisation} ({self.start_date} - {self.end_date if self.end_date else 'onbepaald'})"

    class Meta:
        verbose_name = "Contract"
        verbose_name_plural = "Contracts"


class UserProfile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, null=True, blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.user.username


class InviteUser(models.Model):
    """This model is used as top level orchestrator of the invitation process.
    When an instance is created, a nens_auth_client.models.Invitation is created.
    After the user has accepted the invitation, a UserProfile is created,
    with the organisation set to the organisation of the InviteUser.

    This was done to prevent the need for changes in the nens_auth_client app.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, null=True, blank=False
    )
    nens_auth_client_invitation = models.ForeignKey(
        Invitation,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        help_text="Do not fill in this one!",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.email

    def get_status(self):
        INVITATION_STATUS_CHOICES = [
            (0, "Pending"),
            (1, "Accepted"),
            (2, "Rejected"),
            (3, "Revoked"),
            (4, "Failed"),
        ]
        if self.nens_auth_client_invitation:
            return INVITATION_STATUS_CHOICES[self.nens_auth_client_invitation.status][1]


class ImportTask(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, null=True, blank=True
    )
    bro_domain = models.CharField(
        max_length=3, choices=choices.BRO_DOMAIN_CHOICES, default=None
    )
    kvk_number = models.CharField(max_length=8, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=choices.STATUS_CHOICES, default="PENDING", blank=False
    )
    log = models.TextField(blank=True)
    progress = models.FloatField(blank=True, null=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)
        if self.status == "PENDING":
            # Start the celery task
            tasks.import_bro_data_task.delay(self.uuid)

    def __str__(self) -> str:
        return f"{self.bro_domain} import - {self.data_owner}"


class UploadTask(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True
    )
    bro_domain = models.CharField(
        max_length=3, choices=choices.BRO_DOMAIN_CHOICES, default=None
    )
    project_number = models.CharField(max_length=20, blank=False)
    registration_type = models.CharField(
        blank=False, max_length=235, choices=choices.REGISTRATION_TYPE_OPTIONS
    )
    request_type = models.CharField(
        blank=False, max_length=235, choices=choices.REQUEST_TYPE_OPTIONS
    )
    metadata = JSONField("Metadata", default=dict, blank=False)
    sourcedocument_data = JSONField("Sourcedocument data", default=dict, blank=False)
    status = models.CharField(
        max_length=20, choices=choices.STATUS_CHOICES, default="PENDING", blank=False
    )
    log = models.TextField(blank=True)
    bro_errors = models.TextField(blank=True)
    progress = models.FloatField(blank=True, null=True)
    bro_id = models.CharField(max_length=500, blank=True, null=True)
    bro_delivery_url = models.CharField(max_length=500, blank=True, null=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        super().save(*args, **kwargs)
        if self.status == "PENDING" and self.data_owner:
            # Accessing the authenticated user's username and token
            username = self.data_owner.bro_user_token
            password = self.data_owner.bro_user_password

            # Start the celery task
            tasks.upload_bro_data_task.delay(self.uuid, username, password)

    def __str__(self) -> str:
        return f"{self.data_owner}: {self.registration_type} ({self.request_type})"


class BulkUpload(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True
    )
    project_number = models.CharField(max_length=20, blank=False)
    bulk_upload_type = models.CharField(
        max_length=3,
        choices=choices.BULK_UPLOAD_TYPES,
        default=None,
        blank=False,
        help_text="Determines which process/task to start.",
    )
    request_type = models.CharField(
        blank=False,
        max_length=235,
        choices=choices.REQUEST_TYPE_OPTIONS,
        default="registration",
    )
    metadata = JSONField(
        "Metadata",
        default=dict,
        blank=False,
        help_text="Optional json field to add extra data that is not provided within the files, but is required in the processing of the files.",
    )
    sourcedocument_data = JSONField("Sourcedocument data", default=dict, blank=False)
    status = models.CharField(
        max_length=20, choices=choices.STATUS_CHOICES, default="PENDING", blank=False
    )
    log = models.TextField(blank=True)
    progress = models.FloatField(blank=True, null=True)
    file = models.ForeignKey(
        "UploadFile", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self) -> str:
        return f"{self.data_owner}: Bulk upload {self.bulk_upload_type}"


class UploadFile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    data_owner = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True
    )
    bulk_upload = models.ForeignKey(BulkUpload, on_delete=models.CASCADE, blank=True)
    file = models.FileField(
        upload_to="bulk_uploads/",
        validators=[FileExtensionValidator(allowed_extensions=["csv", "xls", "xlsx"])],
    )

    def __str__(self) -> str:
        return str(self.file)
