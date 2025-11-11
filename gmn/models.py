import random
import uuid
from typing import Any

from django.db import models

from .choices import GMN_EVENT_TYPES


def generate_random_color() -> str:
    """Generate a random hex color code."""
    return f"#{random.randint(0, 0xFFFFFF):06x}"


class GMN(models.Model):
    """Groundwater Monitoring Network

    The abbreviation GMN was intentionally chosen, as it is the commonly used term in BRO land.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    internal_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Alleen beschikbaar voor de eigenaar van de put.",
    )
    bro_id = models.CharField(max_length=18)
    delivery_accountable_party = models.CharField(max_length=8, null=True)
    quality_regime = models.CharField(max_length=10, null=True)
    name = models.CharField(max_length=100, null=True)
    delivery_context = models.CharField(max_length=100, null=True)
    monitoring_purpose = models.CharField(max_length=100, null=True)
    groundwater_aspect = models.CharField(max_length=100, null=True)
    start_date_monitoring = models.DateField(null=True)
    object_registration_time = models.DateTimeField(null=True)
    registration_status = models.CharField(max_length=50, null=True)
    color = models.CharField(max_length=7, null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.bro_id

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.color:
            self.color = generate_random_color()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "GMN's"


class Measuringpoint(models.Model):
    """A measuringpoint is linked to a GMN.

    However, a measuring point is NOT a physical measuring point,
    but rather an abstraction of it. It is linked to a physical GMW monitoringtube,
    which can be replaced.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gmn = models.ForeignKey(
        GMN, on_delete=models.CASCADE, related_name="measuring_points"
    )
    event_type = models.CharField(choices=GMN_EVENT_TYPES, max_length=50, null=True)
    measuringpoint_code = models.CharField(max_length=50, null=True)
    measuringpoint_start_date = models.DateField(null=True)
    measuringpoint_end_date = models.DateField(null=True)
    gmw_bro_id = models.CharField(max_length=50, null=True)
    tube_number = models.CharField(max_length=50, null=True)
    tube_start_date = models.DateField(null=True)
    tube_end_date = models.DateField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.measuringpoint_code

    class Meta:
        verbose_name_plural = "Measuring Points"


class IntermediateEvent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gmn = models.ForeignKey(GMN, on_delete=models.CASCADE)
    event_type = models.CharField(choices=GMN_EVENT_TYPES, max_length=50, null=True)
    event_date = models.DateField(null=False)
    measuringpoint_code = models.CharField(max_length=254, null=False)
    gmw_bro_id = models.CharField(max_length=30, null=False)
    tube_number = models.IntegerField(null=False)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def gmn_bro_id(self):
        return self.gmn.bro_id

    def __str__(self) -> str:
        return f"{self.measuringpoint_code}_{self.event_type}_{self.event_date}"

    class Meta:
        verbose_name_plural = "Intermediate Events"
