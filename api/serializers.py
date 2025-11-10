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
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Exclude sensitive fields
        representation.pop("bro_user_token", None)
        representation.pop("bro_user_password", None)
        representation.pop("request_count", None)
        return representation


class OrganisationCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = api_models.Organisation
        fields = ["bro_user_token", "bro_user_password"]


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
    organisation_url = serializers.CharField()
    kvk = serializers.CharField()
    organisation_current_request_count = serializers.IntegerField()
    bro_credentials_set = serializers.BooleanField()


class ImportTaskSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = api_models.ImportTask
        fields = "__all__"


class UploadTaskSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = api_models.UploadTask
        fields = "__all__"
        read_only_fields = ["data_owner"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Check if this is a list view
        view = self.context.get("view", None)
        is_list_view = hasattr(view, "action") and view.action == "list"

        # Remove 'sourcedocument_data' only in list view when registration_type is "GLD_Addition"

        if is_list_view and representation.get("registration_type") == "GLD_Addition":
            src_data = representation.get("sourcedocument_data", {})
            if "timeValuePairs" not in src_data.keys():
                return representation

            tvps = src_data.pop("timeValuePairs", [])
            src_data["timeValuePairsCount"] = len(tvps)
            representation["sourcedocument_data"] = src_data

        elif is_list_view and representation.get("registration_type") == "GAR":
            src_data = representation.get("sourcedocument_data", {})
            field_measurements = src_data["fieldResearch"].pop("fieldMeasurements", [])
            src_data["fieldResearch"]["fieldMeasurementsCount"] = len(
                field_measurements
            )
            representation["sourcedocument_data"] = src_data

            for analysis in src_data.get("laboratoryAnalyses", []):
                analysis_processes = analysis.pop("analysisProcesses", [])
                for process in analysis_processes:
                    analyses = process.pop("analyses", [])
                    process["analysesCount"] = len(analyses)

                analysis["analysisProcesses"] = analysis_processes

            src_data["laboratoryAnalysesCount"] = len(
                src_data.get("laboratoryAnalyses", [])
            )
            representation["sourcedocument_data"] = src_data

        return representation


class UploadTaskOverviewSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = api_models.UploadTask
        fields = [
            "uuid",
            "status",
            "bro_domain",
            "registration_type",
            "request_type",
            "created",
            "log",
            "bro_errors",
        ]


class BulkUploadSerializer(UrlFieldMixin, serializers.ModelSerializer):
    fieldwork_file = serializers.FileField(write_only=True, required=False)
    lab_file = serializers.FileField(write_only=True, required=False)
    measurement_tvp_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = api_models.BulkUpload
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Check if this is a list view
        view = self.context.get("view", None)
        is_list_view = hasattr(view, "action") and view.action == "list"

        # Remove 'sourcedocument_data' only in list view when registration_type is "GLD_Addition"
        if is_list_view and representation.get("bulk_upload_type") == "GLD":
            src_data = representation.get("sourcedocument_data", {})
            if "timeValuePairs" in src_data:
                tvps = src_data.pop("timeValuePairs")
                src_data["timeValuePairsCount"] = len(tvps)
                representation["sourcedocument_data"] = src_data

        return representation

    def validate(self, attrs):
        fieldwork_file = attrs.get("fieldwork_file")
        lab_file = attrs.get("lab_file")
        measurement_tvp_file = attrs.get("measurement_tvp_file")
        bulk_upload_type = attrs.get("bulk_upload_type")
        file = attrs.get("file")

        # Check if either both fieldwork_file and lab_file are present
        # or measurement_tvp_file is present
        if bulk_upload_type == "GAR" and not (fieldwork_file and lab_file):
            raise serializers.ValidationError(
                "Both 'fieldwork_file' and 'lab_file' must be provided, when a GAR bulk-upload is requested."
            )
        elif bulk_upload_type == "GLD" and not (measurement_tvp_file or file):
            raise serializers.ValidationError(
                "A 'measurement_tvp_file' must be provided, when a GLD bulk-upload is requested."
            )
        elif bulk_upload_type == "GMN" and not (measurement_tvp_file or file):
            raise serializers.ValidationError(
                "A 'measurement_tvp_file' must be provided, when a GMN bulk-upload is requested."
            )
        return attrs

    def create(self, validated_data):
        # Remove the files for the upload creation.
        validated_data.pop("fieldwork_file", None)
        validated_data.pop("lab_file", None)
        validated_data.pop("measurement_tvp_file", None)
        bulk_upload = api_models.BulkUpload.objects.create(**validated_data)

        return bulk_upload
