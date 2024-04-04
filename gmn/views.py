from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions

from api import mixins

from . import models as gmn_models
from . import serializers


class GMNListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.GMNSerializer
    queryset = gmn_models.GMN.objects.all().order_by("-created")

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"


class GMNDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gmn_models.GMN.objects.all()
    serializer_class = serializers.GMNSerializer
    lookup_field = "uuid"

    permission_classes = [permissions.IsAuthenticated]


class MeasuringpointListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.MeasuringpointSerializer
    queryset = gmn_models.Measuringpoint.objects.all().order_by("-created")

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"


class MeasuringpointDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gmn_models.Measuringpoint.objects.all()
    serializer_class = serializers.MeasuringpointSerializer
    lookup_field = "uuid"

    permission_classes = [permissions.IsAuthenticated]
