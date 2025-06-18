from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from frd.models import FRD


class FRDSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = FRD
        fields = "__all__"


class FRDIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FRD
        fields = [
            "uuid",
            "bro_id",
            "delivery_accountable_party",
            "data_owner",
        ]
