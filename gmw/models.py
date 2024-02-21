import uuid
from django.db import models
from api.models import Organisation


class GMW(models.Model):
    """Groundwater Monitoring Well

    The abbreviation GMW was intentionally chosen, as it is the commonly used term in BRO land.
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
    delivery_context = models.CharField(max_length=100, blank=True, null=True)
    construction_standard = models.CharField(max_length=100, blank=True, null=True)
    initial_function = models.CharField(max_length=100, blank=True, null=True)
    removed = models.CharField(max_length=100, blank=True, null=True)
    ground_level_stable = models.CharField(max_length=100, blank=True, null=True)
    well_stability = models.CharField(max_length=100, blank=True, null=True)
    nitg_code = models.CharField(max_length=100, blank=True, null=True)
    well_code = models.CharField(max_length=100, blank=True, null=True)
    owner = models.CharField(max_length=100, blank=True, null=True)
    well_head_protector = models.CharField(max_length=100, blank=True, null=True)
    delivered_location = models.CharField(max_length=100, blank=True, null=True)
    local_vertical_reference_point = models.CharField(
        max_length=100, blank=True, null=True
    )
    offset = models.CharField(max_length=100, blank=True, null=True)
    vertical_datum = models.CharField(max_length=100, blank=True, null=True)
    ground_level_position = models.CharField(max_length=100, blank=True, null=True)
    ground_level_positioning_method = models.CharField(
        max_length=100, blank=True, null=True
    )
    standardized_location = models.CharField(max_length=100, blank=True, null=True)
    object_registration_time = models.DateTimeField(blank=True, null=True)
    registration_status = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.bro_id

    class Meta:
        verbose_name_plural = "GMW's"


class MonitoringTube(models.Model):
    """A monitoringtube is part of a GMW."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        Organisation, on_delete=models.SET_NULL, null=True, blank=True
    )
    gmw = models.ForeignKey(GMW, on_delete=models.CASCADE, null=True, blank=True)
    tube_number = models.CharField(max_length=100, blank=True, null=True)
    tube_type = models.CharField(max_length=100, blank=True, null=True)
    artesian_well_cap_present = models.CharField(max_length=100, blank=True, null=True)
    sediment_sump_present = models.CharField(max_length=100, blank=True, null=True)
    number_of_geo_ohm_cables = models.CharField(max_length=100, blank=True, null=True)
    tube_top_diameter = models.CharField(max_length=100, blank=True, null=True)
    variable_diameter = models.CharField(max_length=100, blank=True, null=True)
    tube_status = models.CharField(max_length=100, blank=True, null=True)
    tube_top_position = models.CharField(max_length=100, blank=True, null=True)
    tube_top_positioning_method = models.CharField(
        max_length=100, blank=True, null=True
    )
    tube_part_inserted = models.CharField(max_length=100, blank=True, null=True)
    tube_in_use = models.CharField(max_length=100, blank=True, null=True)
    tube_packing_material = models.CharField(max_length=100, blank=True, null=True)
    tube_material = models.CharField(max_length=100, blank=True, null=True)
    glue = models.CharField(max_length=100, blank=True, null=True)
    screen_length = models.CharField(max_length=100, blank=True, null=True)
    sock_material = models.CharField(max_length=100, blank=True, null=True)
    screen_top_position = models.CharField(max_length=100, blank=True, null=True)
    screen_bottom_position = models.CharField(max_length=100, blank=True, null=True)
    plain_tube_part_length = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.gmw}-{self.tube_number}"
