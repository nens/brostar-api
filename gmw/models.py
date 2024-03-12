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
        Organisation, on_delete=models.CASCADE,
    )
    bro_id = models.CharField(max_length=18)
    delivery_accountable_party = models.CharField(max_length=8)
    quality_regime = models.CharField(max_length=50)
    delivery_context = models.CharField(max_length=100)
    construction_standard = models.CharField(max_length=100)
    initial_function = models.CharField(max_length=100)
    removed = models.CharField(max_length=100)
    ground_level_stable = models.CharField(max_length=100)
    well_stability = models.CharField(max_length=100)
    nitg_code = models.CharField(max_length=100)
    well_code = models.CharField(max_length=100)
    owner = models.CharField(max_length=100)
    well_head_protector = models.CharField(max_length=100)
    delivered_location = models.CharField(max_length=100)
    local_vertical_reference_point = models.CharField(
        max_length=100,
    )
    offset = models.CharField(max_length=100)
    vertical_datum = models.CharField(max_length=100)
    ground_level_position = models.CharField(max_length=100)
    ground_level_positioning_method = models.CharField(
        max_length=100,
    )
    standardized_location = models.CharField(max_length=100)
    object_registration_time = models.DateTimeField()
    registration_status = models.CharField(max_length=50)

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
        Organisation, on_delete=models.CASCADE,
    )
    gmw = models.ForeignKey(GMW, on_delete=models.CASCADE)
    tube_number = models.CharField(max_length=100)
    tube_type = models.CharField(max_length=100)
    artesian_well_cap_present = models.CharField(max_length=100)
    sediment_sump_present = models.CharField(max_length=100)
    number_of_geo_ohm_cables = models.CharField(max_length=100)
    tube_top_diameter = models.CharField(max_length=100)
    variable_diameter = models.CharField(max_length=100)
    tube_status = models.CharField(max_length=100)
    tube_top_position = models.CharField(max_length=100)
    tube_top_positioning_method = models.CharField(
        max_length=100,
    )
    tube_part_inserted = models.CharField(max_length=100)
    tube_in_use = models.CharField(max_length=100)
    tube_packing_material = models.CharField(max_length=100)
    tube_material = models.CharField(max_length=100)
    glue = models.CharField(max_length=100)
    screen_length = models.CharField(max_length=100)
    sock_material = models.CharField(max_length=100)
    screen_top_position = models.CharField(max_length=100)
    screen_bottom_position = models.CharField(max_length=100)
    plain_tube_part_length = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.gmw}-{self.tube_number}"
