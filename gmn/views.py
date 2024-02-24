from rest_framework import generics, status
from rest_framework.response import Response
from . import serializers
from . import models
from api import mixins
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions


class GMNListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.GMNSerializer
    queryset = models.GMN.objects.all()

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"

class GMNDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = models.GMN.objects.all()
    serializer_class = serializers.GMNSerializer
    lookup_field = "uuid"

    permission_classes = [permissions.IsAuthenticated]


class MeasuringpointListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.MeasuringpointSerializer
    queryset = models.Measuringpoint.objects.all()

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"

class MeasuringpointDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = models.Measuringpoint.objects.all()
    serializer_class = serializers.MeasuringpointSerializer
    lookup_field = "uuid"

    permission_classes = [permissions.IsAuthenticated]

