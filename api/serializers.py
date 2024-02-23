from rest_framework import serializers

from . import models
from .mixins import UrlFieldMixin



class UserProfileSerializer(UrlFieldMixin, serializers.ModelSerializer):
    credentials_set = serializers.SerializerMethodField()
    organisation_name = serializers.SerializerMethodField()
    organisation_kvk = serializers.SerializerMethodField()
    
    class Meta:
        model = models.UserProfile
        exclude = ["user"]

    # Exclude token and password in the get requests
    def to_representation(self, instance):
        if self.context['request'].method == 'GET':
            exclude_fields = ["bro_user_token", "bro_user_password"]
            for field in exclude_fields:
                self.fields.pop(field, None)
        return super().to_representation(instance)
    
    def get_credentials_set(self, obj):
        """Return the value of the credentials_set property."""
        return obj.credentials_set
    
    def get_organisation_name(self, obj):
        organisation = obj.organisation
        return organisation.name if organisation else None
    
    def get_organisation_kvk(self, obj):
        organisation = obj.organisation
        return organisation.kvk_number if organisation else None
    
    
    
class ImportTaskSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.ImportTask
        fields = "__all__"


class UploadTaskSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.UploadTask
        fields = "__all__"
