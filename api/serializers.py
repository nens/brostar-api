from rest_framework import serializers
from . import models


class ImportTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ImportTask
        fields = "__all__"
