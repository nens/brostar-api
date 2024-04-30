import uuid
from typing import Any

from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import JSONField
from encrypted_model_fields.fields import EncryptedCharField

from api import choices, tasks


class Organisation(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    kvk_number = models.CharField(max_length=8)
    bro_user_token = EncryptedCharField(max_length=100, blank=True, null=True)
    bro_user_password = EncryptedCharField(max_length=100, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


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
        if self.status == "PENDING":
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
        help_text="Determines which process/task to start.",
    )
    metadata = JSONField(
        "Metadata",
        default=dict,
        blank=True,
        help_text="Optional json field to add extra data that is not provided within the files, but is required in the processing of the files.",
    )
    status = models.CharField(
        max_length=20, choices=choices.STATUS_CHOICES, default="PENDING", blank=False
    )
    log = models.TextField(blank=True)
    progress = models.FloatField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.data_owner}: Bulk upload {self.bulk_upload_type}"


class UploadFile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    data_owner = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True
    )
    bulk_upload = models.ForeignKey(BulkUpload, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to="bulk_uploads/",
        validators=[FileExtensionValidator(allowed_extensions=["csv", "xls", "xlsx"])],
    )

    def __str__(self) -> str:
        return str(self.uuid)
