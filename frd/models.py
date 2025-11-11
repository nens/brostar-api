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
    delivery_accountable_party = models.CharField(max_length=8, null=True)
    quality_regime = models.CharField(max_length=100, null=True)
    gmw_bro_id = models.CharField(max_length=100, null=True)
    tube_number = models.CharField(max_length=100, null=True)
    research_first_date = models.DateField(null=True, blank=True)
    research_last_date = models.DateField(null=True, blank=True)
    data_owner = models.ForeignKey("api.Organisation", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return self.bro_id

    class Meta:
        verbose_name_plural = "FRD's"
