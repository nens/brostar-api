from django.contrib.auth.models import User
from django.db import models

class GMN(models.Model):
    """The abbreviation GMN was intentionally chosen because it is the BRO term that is never used in full."""
    bro_id = models.CharField(max_length=18)

    def __str__(self):
        return self.bro_id
