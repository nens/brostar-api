from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin

from . import models as gmw_models


class GMWSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = gmw_models.GMW
        fields = "__all__"


class MonitoringTubeSerializer(
    UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer
):
    class Meta:
        model = gmw_models.MonitoringTube
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
