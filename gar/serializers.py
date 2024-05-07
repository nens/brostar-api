from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from gmw import models as gmw_models

from . import models


class GARSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    gmw_nitg_code = serializers.SerializerMethodField()

    class Meta:
        model = models.GAR
        fields = "__all__"

    def get_gmw_nitg_code(self, obj: models.GAR) -> str:
        try:
            return gmw_models.GMW.objects.get(bro_id=obj.gmw_bro_id).nitg_code
        except ObjectDoesNotExist:
            return None
