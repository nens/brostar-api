from rest_framework import serializers
from django.contrib.auth.models import User

from . import models as api_models
from .mixins import UrlFieldMixin

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

class ImportTaskSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = api_models.ImportTask
        fields = "__all__"


class UploadTaskSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = api_models.UploadTask
        fields = "__all__"
