from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from gld.models import GLD


class GLDSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = GLD
        fields = "__all__"
