import uuid

from django.db import models


class GMN(models.Model):
    """The abbreviation GMN was intentionally chosen because it is the BRO term that is never used in full."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bro_id = models.CharField(max_length=18)

    def __str__(self):
        return self.bro_id

    class Meta:
        verbose_name_plural = "GMN's"
