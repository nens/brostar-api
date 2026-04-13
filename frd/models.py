import uuid

from django.db import models
from django.db.models import JSONField


class FRD(models.Model):
    """Formation Resistance Dossier

    The abbreviation FRD was intentionally chosen, as it is the commonly used term in BRO land.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    internal_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Alleen beschikbaar voor de eigenaar van de put.",
    )
    bro_id = models.CharField(max_length=18)
    linked_gmns = JSONField(
        "Gmns", default=list, blank=False
    )  # In GLD XMLs these are actually returned.

    # Added to speed up queries
    monitoring_tube = models.ForeignKey(
        "gmw.MonitoringTube",
        on_delete=models.CASCADE,
        related_name="formation_resistance_dossiers",
        null=True,
        blank=True,
    )

    delivery_accountable_party = models.CharField(max_length=8, null=True)
    quality_regime = models.CharField(max_length=100, null=True)
    determination_type = models.CharField(max_length=100, null=True)
    gmw_bro_id = models.CharField(max_length=100, null=True)
    tube_number = models.CharField(max_length=100, null=True)
    research_first_date = models.DateField(null=True, blank=True)
    research_last_date = models.DateField(null=True, blank=True)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.bro_id

    class Meta:
        verbose_name_plural = "FRD's"


class MeasurementConfiguration(models.Model):
    """Electrode configuration used during a geo-electric measurement."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    frd = models.ForeignKey(
        FRD, on_delete=models.CASCADE, related_name="measurement_configurations"
    )
    measurement_configuration_id = models.CharField(max_length=50)
    measurement_pair = JSONField(null=True, blank=True)
    current_pair = JSONField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Measurement configurations"

    def __str__(self) -> str:
        return f"{self.measurement_configuration_id} for {self.frd.bro_id}"


class GeoElectricMeasurement(models.Model):
    """A single geo-electric field measurement event for an FRD."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    frd = models.ForeignKey(
        FRD, on_delete=models.CASCADE, related_name="geo_electric_measurements"
    )
    measurement_date = models.DateField(null=True, blank=True)
    determination_procedure = models.CharField(max_length=100, null=True)
    evaluation_procedure = models.CharField(max_length=100, null=True)

    class Meta:
        verbose_name_plural = "Geo-electric measurements"

    def __str__(self) -> str:
        return f"{self.measurement_date} for {self.frd.bro_id}"


class GeoElectricMeasure(models.Model):
    """A single resistance value within a GeoElectricMeasurement."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    geo_electric_measurement = models.ForeignKey(
        GeoElectricMeasurement, on_delete=models.CASCADE, related_name="measures"
    )
    resistance = models.CharField(max_length=50, null=True)
    related_measurement_configuration = models.CharField(max_length=50, null=True)

    class Meta:
        verbose_name_plural = "Geo-electric measures"

    def __str__(self) -> str:
        return (
            f"Resistance {self.resistance} ({self.related_measurement_configuration})"
        )


class CalculatedApparentFormationResistance(models.Model):
    """Calculated apparent formation resistance series for a geo-electric measurement."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    geo_electric_measurement = models.OneToOneField(
        GeoElectricMeasurement,
        on_delete=models.CASCADE,
        related_name="calculated_apparent_formation_resistance",
    )
    evaluation_procedure = models.CharField(max_length=100, null=True)
    values = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Calculated apparent formation resistances"

    def __str__(self) -> str:
        return f"Calculated resistance for {self.geo_electric_measurement}"
