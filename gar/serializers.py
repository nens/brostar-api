from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from rest_framework import serializers

from api.mixins import RequiredFieldsMixin, UrlFieldMixin
from gmw import models as gmw_models

from . import models as gar_models


class GARSerializer(UrlFieldMixin, RequiredFieldsMixin, serializers.ModelSerializer):
    gmw_nitg_code = serializers.SerializerMethodField()

    class Meta:
        model = gar_models.GAR
        fields = "__all__"

    def get_gmw_nitg_code(self, obj: gar_models.GAR) -> str:
        try:
            return gmw_models.GMW.objects.get(bro_id=obj.gmw_bro_id).nitg_code
        except ObjectDoesNotExist:
            return None

        except MultipleObjectsReturned:
            return (
                gmw_models.GMW.objects.filter(bro_id=obj.gmw_bro_id).first().nitg_code
            )


class GARIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = gar_models.GAR
        fields = [
            "uuid",
            "bro_id",
            "delivery_accountable_party",
            "data_owner",
        ]
