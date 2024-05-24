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
