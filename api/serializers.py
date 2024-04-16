from django.contrib.auth.models import User
from rest_framework import serializers

from api import models as api_models

from .mixins import UrlFieldMixin


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


# Only used for swagger definitions
class UserLoggedInSerializer(serializers.Serializer):
    logged_in = serializers.BooleanField()
    login_url = serializers.URLField(max_length=200)
    logout_url = serializers.URLField(max_length=200)
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.CharField()
    organisation = serializers.CharField()
    kvk = serializers.CharField()


class ImportTaskSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = api_models.ImportTask
        fields = "__all__"


class UploadTaskSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = api_models.UploadTask
        fields = "__all__"