import uuid

from django.contrib.auth.models import User
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

    def __str__(self):
        return self.user.username


class ImportTask(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    BRO_OBJECT_CHOICES = [
        ("GMN", "GMN"),
        ("GMW", "GMW"),
        ("GLD", "GLD"),
        ("FRD", "FRD"),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bro_object_type = models.CharField(
        max_length=3, choices=BRO_OBJECT_CHOICES, default=None
    )
    organisation = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING", blank=True
    )
    log = models.TextField(blank=True)

    def __str__(self):
        return f"{self.bro_object} import - {self.organisation} ({self.created_at})"
