import uuid

from django.db import models
from django.db.models import JSONField, Manager


class GMW(models.Model):
    """Groundwater Monitoring Well

    The abbreviation GMW was intentionally chosen, as it is the commonly used term in BRO land.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        "api.Organisation",
        on_delete=models.CASCADE,
    )
    bro_id = models.CharField(max_length=18)
    delivery_accountable_party = models.CharField(max_length=8, null=True)
    quality_regime = models.CharField(max_length=50, null=True)
    well_construction_date = models.CharField(max_length=100, null=True)
    delivery_context = models.CharField(max_length=100, null=True)
    construction_standard = models.CharField(max_length=100, null=True)
    initial_function = models.CharField(max_length=100, null=True)
    removed = models.CharField(max_length=100, null=True)
    ground_level_stable = models.CharField(max_length=100, null=True)
    well_stability = models.CharField(max_length=100, null=True, blank=True)
    nitg_code = models.CharField(max_length=100, null=True, blank=True)
    well_code = models.CharField(max_length=100, null=True)
    owner = models.CharField(max_length=100, null=True, blank=True)
    well_head_protector = models.CharField(max_length=100, null=True)
    delivered_location = models.CharField(max_length=100, null=True)
    horizontal_positioning_method = models.CharField(max_length=100, null=True)
    local_vertical_reference_point = models.CharField(max_length=100, null=True)
    offset = models.CharField(max_length=100, null=True)
    vertical_datum = models.CharField(max_length=100, null=True)
    ground_level_position = models.CharField(max_length=100, null=True, blank=True)
    ground_level_positioning_method = models.CharField(max_length=100, null=True)
    standardized_location = models.CharField(max_length=100, null=True)
    object_registration_time = models.DateTimeField(null=True)
    registration_status = models.CharField(max_length=50, null=True)

    tubes = Manager["MonitoringTube"]
    events = Manager["Event"]

    def __str__(self) -> str:
        return self.bro_id

    class Meta:
        verbose_name_plural = "GMW's"

    @property
    def nr_of_tubes(self) -> int:
        return self.tubes.count()

    @property
    def nr_of_intermediate_events(self) -> int:
        return self.events.count()


class MonitoringTube(models.Model):
    """A monitoringtube is part of a GMW."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gmw = models.ForeignKey(
        GMW, on_delete=models.CASCADE, null=False, related_name="tubes"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        "api.Organisation",
        on_delete=models.CASCADE,
    )
    tube_number = models.CharField(max_length=100, null=True)
    tube_type = models.CharField(max_length=100, null=True)
    artesian_well_cap_present = models.CharField(max_length=100, null=True)
    sediment_sump_present = models.CharField(max_length=100, null=True)
    sediment_sump_length = models.CharField(max_length=100, null=True, blank=True)
    number_of_geo_ohm_cables = models.CharField(max_length=100, null=True)
    geo_ohm_cables = JSONField("Geoohm Cables", default=dict, blank=True)
    tube_top_diameter = models.CharField(max_length=100, null=True, blank=True)
    variable_diameter = models.CharField(max_length=100, null=True)
    tube_status = models.CharField(max_length=100, null=True)
    tube_top_position = models.CharField(max_length=100, null=True)
    tube_top_positioning_method = models.CharField(max_length=100, null=True)
    tube_part_inserted = models.CharField(max_length=100, null=True)
    tube_in_use = models.CharField(max_length=100, null=True)
    tube_packing_material = models.CharField(max_length=100, null=True)
    tube_material = models.CharField(max_length=100, null=True)
    glue = models.CharField(max_length=100, null=True)
    screen_length = models.CharField(max_length=100, null=True)
    screen_protection = models.CharField(max_length=100, null=True, blank=True)
    sock_material = models.CharField(max_length=100, null=True)
    screen_top_position = models.CharField(max_length=100, null=True)
    screen_bottom_position = models.CharField(max_length=100, null=True)
    plain_tube_part_length = models.CharField(max_length=100, null=True)

    def __str__(self) -> str:
        return f"{self.gmw}-{self.tube_number}"

    class Meta:
        verbose_name_plural = "Monitoring Tubes"


class Event(models.Model):
    """A event is a change after a period of time to a GMW or its monitoring tube(s)."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gmw = models.ForeignKey(
        GMW, on_delete=models.CASCADE, null=False, related_name="events"
    )
    event_name = models.CharField(
        max_length=40,
    )
    event_date = models.DateField()
    metadata = JSONField("Metadata", default=dict, blank=False)
    sourcedocument_data = JSONField("Sourcedocument data", default=dict, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey(
        "api.Organisation",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name_plural = "Events"
