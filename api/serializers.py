from django.contrib.auth.models import User
from rest_framework import serializers

from api import models as api_models

from .mixins import UrlFieldMixin


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Organisation
        fields = ["name", "kvk_number"]


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


class BulkUploadSerializer(UrlFieldMixin, serializers.ModelSerializer):
    fieldwork_file = serializers.FileField(write_only=True, required=True)
    lab_file = serializers.FileField(write_only=True, required=True)

    class Meta:
        model = api_models.BulkUpload
        fields = "__all__"

    def create(self, validated_data):
        fieldwork_file = validated_data.pop("fieldwork_file", None)
        lab_file = validated_data.pop("lab_file", None)
        bulk_upload = api_models.BulkUpload.objects.create(**validated_data)

        if fieldwork_file:
            api_models.UploadFile.objects.create(
                bulk_upload=bulk_upload, file=fieldwork_file
            )
        if lab_file:
            api_models.UploadFile.objects.create(bulk_upload=bulk_upload, file=lab_file)

        return bulk_upload
