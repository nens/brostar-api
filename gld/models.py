import uuid

from django.db import models


class GLD(models.Model):
    """Groundwater Level Dossier

    The abbreviation GLD was intentionally chosen, as it is the commonly used term in BRO land.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)
    bro_id = models.CharField(max_length=18)
    delivery_accountable_party = models.CharField(max_length=8, null=True)
    quality_regime = models.CharField(max_length=100, null=True)
    gmw_bro_id = models.CharField(max_length=100, null=True)
    tube_number = models.CharField(max_length=100, null=True)
    research_first_date = models.DateField(null=True, blank=True)
    research_last_date = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return self.bro_id

    class Meta:
        verbose_name_plural = "GLD's"


class Observation(models.Model):
    """Observation

    The timeseries, with a quality label and type. Linked to a GLD.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)
    observation_id = models.CharField(max_length=100)
    begin_position = models.CharField(max_length=100, null=True)
    end_position = models.CharField(max_length=100, null=True)
    result_time = models.CharField(max_length=100, null=True)
    validation_status = models.CharField(max_length=100, null=True)
    investigator_kvk = models.CharField(max_length=100, null=True)
    observation_type = models.CharField(max_length=100, null=True)
    process_reference = models.CharField(max_length=100, null=True)
    air_pressure_compensation_type = models.CharField(max_length=100, null=True)
    evaluation_procedure = models.CharField(max_length=100, null=True)
    measurement_instrument_type = models.CharField(max_length=100, null=True)

    class Meta:
        verbose_name_plural = "Observations"


class MeasurementTvp(models.Model):
    """MEasurement Time-Value Pair

    A single event / measurement on a observation.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)
    time = models.CharField(max_length=100)
    value = models.FloatField(null=True, blank=True)
    status_quality_control = models.CharField(max_length=100, null=True)
    censoring_reason = models.CharField(max_length=100, null=True, blank=True)
    censoring_limit = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Measurement time-value pairs"
