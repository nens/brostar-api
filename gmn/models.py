import uuid

from django.db import models
from api import choices


class GMN(models.Model):
    """Groundwater Monitoring Network
    
    The abbreviation GMN was intentionally chosen, as it is the commonly used term in BRO land."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.bro_id

    class Meta:
        verbose_name_plural = "GMN's"

class Measuringpoint(models.Model):
    """A measuringpoint is a single object in a GMN.
    
    However, a measuring point is NOT a physical measuring point,
    but rather an abstraction of it. It is linked to a physical GMW monitoringtube, 
    which can be replaced.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gmn = models.ForeignKey(GMN, on_delete=models.SET_NULL, null=True, blank=True)
    measuringpoint_code = models.CharField(max_length=50, blank=True, null=True)
    measuringpoint_start_date = models.DateField(blank=True, null=True)
    gmw_bro_id = models.CharField(max_length=50, blank=True, null=True)
    tube_number = models.CharField(max_length=50, blank=True, null=True)
    tube_start_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.measuringpoint_code


class GMNStartregistration(models.Model):
    """GMN Startregistrations"""
    
    REQUEST_TYPE_OPTIONS = {
        "register":"register",
        "replace":"replace",
        "move":"move",
    }

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)   
    request_type = models.CharField(
        blank=False, max_length=235, choices=REQUEST_TYPE_OPTIONS
    )
    request_reference = models.CharField(max_length=150, blank=False)
    delivery_accountable_party = models.CharField(max_length=150, blank=False)
    quality_regime = models.CharField(
        blank=False, max_length=235, choices=choices.QUALITY_REGIME_OPTIONS
    )
    object_id_accountable_party = models.CharField(max_length=150, blank=False)
    name = models.CharField(max_length=150, blank=False)
    delivery_context =  models.CharField(
        blank=False, max_length=235, choices=choices.DELIVERY_CONTEXT_OPTIONS
    )
    monitoring_purpose =  models.CharField(
        blank=False, max_length=235, choices=choices.MONITORING_PURPOSE_OPTIONS
    )
    groundwater_aspect =  models.CharField(
        blank=False, max_length=235, choices=choices.GROUNDWATER_ASPECT_OPTIONS
    )
    start_date_monitoring = models.DateField(blank=False, null=True)

    measuringpoints = models.ForeignKey(Measuringpoint, on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        return self.request_reference