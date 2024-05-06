from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin

from . import models


class GARSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = models.GAR
        fields = "__all__"
