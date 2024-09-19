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
        return gmw_models.GMW.objects.get(bro_id=self.gmw_bro_id).first().nitg_code

    class Meta:
        verbose_name_plural = "GAR's"
