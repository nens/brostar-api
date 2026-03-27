import uuid

from django.db import models


class GPD(models.Model):
    """Ground Water Production Dossier

    The abbreviation GPD was intentionally chosen, as it is the commonly used term in BRO land.
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
    delivery_accountable_party = models.CharField(max_length=8, null=True)
    quality_regime = models.CharField(max_length=100, null=True)

    start_time = models.DateField(null=True, blank=True)
    end_time = models.DateField(null=True, blank=True)

    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.bro_id

    class Meta:
        verbose_name_plural = "GPD's"


class Report(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    gpd = models.ForeignKey(GPD, on_delete=models.CASCADE, related_name="reports")
    report_id = models.CharField(max_length=100)
    method = models.CharField(
        choices=[
            ("berekening", "Berekening"),
            ("watermeter", "Watermeter"),
            ("onbekend", "Onbekend"),
        ],
        max_length=100,
    )
    begin_date = models.DateField()
    end_date = models.DateField()

    groundwater_usage_facility_bro_id = models.CharField(
        max_length=50, null=False, blank=False
    )

    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.report_id


class VolumeSeries(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    report = models.ForeignKey(
        Report, on_delete=models.CASCADE, related_name="volume_series"
    )
    begin_date = models.DateField()
    end_date = models.DateField()
    water_in_out = models.CharField(
        choices=[("ingebracht", "Ingebracht"), ("onttrokken", "Onttrokken")],
        max_length=25,
    )  # 'ingebracht' or 'onttrokken'
    temperature = models.CharField(
        choices=[("warm", "Warm"), ("koud", "Koud"), ("onbekend", "Onbekend")],
        max_length=25,
    )  # 'warm''koud'
    volume = models.FloatField()

    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.report.report_id} - {self.begin_date} to {self.end_date}"
