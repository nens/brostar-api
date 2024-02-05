from django.db import models

class Organisation(models.Model):
    name = models.CharField(max_length=255)
    kvk_number = models.CharField(max_length=8)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
