from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from frd.models import FRD


class FRDSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = FRD
        fields = "__all__"
