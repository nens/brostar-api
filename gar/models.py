import uuid

from django.db import models

from gmw import models as gmw_models


class GAR(models.Model):
    """Groundwater Analysis Research

    The abbreviation GAR was intentionally chosen, as it is the commonly used term in BRO land.
    """

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)
    bro_id = models.CharField(max_length=18)
    delivery_accountable_party = models.CharField(max_length=8, null=True)
    quality_regime = models.CharField(max_length=100, null=True)

    # Added to speed up queries
    monitoring_tube = models.ForeignKey(
        "gmw.MonitoringTube",
        on_delete=models.CASCADE,
        related_name="groundwater_analysis_reports",
        null=True,
        blank=True,
    )

    quality_control_method = models.CharField(max_length=100, null=True)
    gmw_bro_id = models.CharField(max_length=100, null=True)
    tube_number = models.CharField(max_length=100, null=True)
    sampling_datetime = models.DateTimeField(null=True)
    sampling_standard = models.CharField(max_length=100, null=True)
    pump_type = models.CharField(max_length=100, null=True)
    abnormality_in_cooling = models.CharField(max_length=100, null=True)
    abnormality_in_device = models.CharField(max_length=100, null=True)
    polluted_by_engine = models.CharField(max_length=100, null=True)
    filter_aerated = models.CharField(max_length=100, null=True)
    groundwater_level_dropped_too_much = models.CharField(max_length=100, null=True)
    abnormal_filter = models.CharField(max_length=100, null=True)
    sample_aerated = models.CharField(max_length=100, null=True)
    hose_reused = models.CharField(max_length=100, null=True)
    temperature_difficult_to_measure = models.CharField(max_length=100, null=True)
    lab_analysis_date = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return self.bro_id

    @property
    def gmw_nitg_code(self):
        return (
            gmw_models.GMW.objects.all()
            .filter(bro_id=self.gmw_bro_id)
            .first()
            .nitg_code
        )

    class Meta:
        verbose_name_plural = "GAR's"


class FieldSample(models.Model):
    """Field sample taken during a GAR."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gar = models.ForeignKey(GAR, on_delete=models.CASCADE, related_name="field_samples")
    sample_number = models.CharField(max_length=100, null=True)
    sample_depth = models.CharField(max_length=100, null=True)
    sample_type = models.CharField(max_length=100, null=True)

    class Meta:
        verbose_name_plural = "Field samples"

    def __str__(self) -> str:
        return f"Sample {self.sample_number} from {self.gar.bro_id}"


class LaboratoryAnalysis(models.Model):
    """Laboratory analysis performed on a field sample."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gar = models.ForeignKey(
        GAR, on_delete=models.CASCADE, related_name="laboratory_analyses"
    )
    parameter = models.CharField(max_length=100, null=True)
    value = models.CharField(max_length=100, null=True)
    unit = models.CharField(max_length=100, null=True)

    class Meta:
        verbose_name_plural = "Laboratory analyses"

    def __str__(self) -> str:
        return f"{self.parameter} analysis for {self.gar.bro_id}"
