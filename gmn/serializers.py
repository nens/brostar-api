from rest_framework import serializers
from . import models
from api.mixins import UrlFieldMixin

class GMNSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.GMN
        fields = "__all__"

class MeasuringpointSerializer(UrlFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = models.Measuringpoint
        fields = "__all__"

class GMNStartregistrationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GMNStartregistration
        fields = '__all__'