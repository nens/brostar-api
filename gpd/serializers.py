from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from gpd.models import GPD, Report


class GPDSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = GPD
        fields = "__all__"


class GPDIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPD
        fields = [
            "uuid",
            "bro_id",
            "delivery_accountable_party",
            "data_owner",
        ]


class ReportSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = "__all__"
