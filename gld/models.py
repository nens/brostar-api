import uuid

from django.db import models
from django.db.models import JSONField, Manager


class GLD(models.Model):
    """Groundwater Level Dossier

    The abbreviation GLD was intentionally chosen, as it is the commonly used term in BRO land.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    bro_id = models.CharField(max_length=18)
    delivery_accountable_party = models.CharField(max_length=8, null=True)
    linked_gmns = JSONField(
        "Gmns", default=list, blank=False
    )  # In GLD XMLs these are actually returned.
    quality_regime = models.CharField(max_length=100, null=True)
    gmw_bro_id = models.CharField(max_length=100, null=True)
    tube_number = models.CharField(max_length=100, null=True)
    research_first_date = models.DateField(null=True, blank=True)
    research_last_date = models.DateField(null=True, blank=True)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)

    observations = Manager["Observation"]

    def __str__(self) -> str:
        return self.bro_id

    class Meta:
        verbose_name_plural = "GLD's"

    @property
    def nr_of_observations(self) -> int:
        return self.observations.count()


class Observation(models.Model):
    """Observation

    The timeseries, with a quality label and type. Linked to a GLD.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gld = models.ForeignKey(
        GLD, on_delete=models.CASCADE, null=False, related_name="observations"
    )
    observation_id = models.CharField(max_length=100)
    begin_position = models.DateField(max_length=100, null=False)
    end_position = models.DateField(max_length=100, null=False)
    result_time = models.DateTimeField(max_length=100, null=False)
    validation_status = models.CharField(max_length=100, null=True)
    investigator_kvk = models.CharField(max_length=100, null=True)
    observation_type = models.CharField(max_length=100, null=True)
    process_reference = models.CharField(max_length=100, null=True)
    air_pressure_compensation_type = models.CharField(max_length=100, null=True)
    evaluation_procedure = models.CharField(max_length=100, null=True)
    measurement_instrument_type = models.CharField(max_length=100, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)

    measurements = Manager["MeasurementTvp"]

    class Meta:
        verbose_name_plural = "Observations"

    @property
    def nr_of_measurements(self) -> int:
        return self.measurements.count()


class MeasurementTvp(models.Model):
    """Measurement Time-Value Pair

    A single event / measurement on a observation.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    observation = models.ForeignKey(
        Observation, on_delete=models.CASCADE, null=False, related_name="measurements"
    )
    time = models.CharField(max_length=100)
    value = models.FloatField(null=True, blank=True)
    status_quality_control = models.CharField(max_length=100, null=True)
    censoring_reason = models.CharField(max_length=100, null=True, blank=True)
    censoring_limit = models.CharField(max_length=100, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Measurement time-value pairs"
