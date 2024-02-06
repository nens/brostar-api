from rest_framework import serializers
from . import models


class GMNSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GMN
        fields = "__all__"

class MeasuringpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Measuringpoint
        fields = "__all__"
