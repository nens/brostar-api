import uuid

from django.db import models

from api.models import Organisation


class GMN(models.Model):
    """Groundwater Monitoring Network

    The abbreviation GMN was intentionally chosen, as it is the commonly used term in BRO land.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True
    )
    bro_id = models.CharField(max_length=18)
    delivery_accountable_party = models.CharField(max_length=8, blank=True, null=True)
    quality_regime = models.CharField(max_length=50, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    delivery_context = models.CharField(max_length=100, blank=True, null=True)
    monitoring_purpose = models.CharField(max_length=100, blank=True, null=True)
    groundwater_aspect = models.CharField(max_length=100, blank=True, null=True)
    start_date_monitoring = models.DateField(blank=True, null=True)
    object_registration_time = models.DateTimeField(blank=True, null=True)
    registration_status = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.bro_id

    class Meta:
        verbose_name_plural = "GMN's"


class Measuringpoint(models.Model):
    """A measuringpoint is linked to a GMN.

    However, a measuring point is NOT a physical measuring point,
    but rather an abstraction of it. It is linked to a physical GMW monitoringtube,
    which can be replaced.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True
    )
    gmn = models.ForeignKey(GMN, on_delete=models.CASCADE, null=True, blank=True)
    measuringpoint_code = models.CharField(max_length=50, blank=True, null=True)
    measuringpoint_start_date = models.DateField(blank=True, null=True)
    gmw_bro_id = models.CharField(max_length=50, blank=True, null=True)
    tube_number = models.CharField(max_length=50, blank=True, null=True)
    tube_start_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.measuringpoint_code
