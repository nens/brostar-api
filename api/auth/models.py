from django.contrib.auth.models import User
from django.db import models

class Organisation(models.Model):
    name = models.CharField(max_length=255)
    kvk_number = models.CharField(max_length=8)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.ForeignKey('Organisation', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username

