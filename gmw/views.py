from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions

from api import mixins

from . import models as gmw_models
from . import serializers


class GMWListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.GMWSerializer
    queryset = gmw_models.GMW.objects.all()

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"


class GMWDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gmw_models.GMW.objects.all()
    serializer_class = serializers.GMWSerializer
    lookup_field = "uuid"

    permission_classes = [permissions.IsAuthenticated]


class MonitoringTubeListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.MonitoringTubeSerializer
    queryset = gmw_models.MonitoringTube.objects.all()

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"


class MonitoringTubeDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gmw_models.MonitoringTube.objects.all()
    serializer_class = serializers.MonitoringTubeSerializer
    lookup_field = "uuid"

    permission_classes = [permissions.IsAuthenticated]
