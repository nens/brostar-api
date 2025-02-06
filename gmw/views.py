from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import filters, serializers
from . import models as gmw_models


class GMWListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.GMWSerializer
    queryset = gmw_models.GMW.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GmwFilter
    filterset_fields = "__all__"


class GMWDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gmw_models.GMW.objects.all()
    serializer_class = serializers.GMWSerializer
    lookup_field = "uuid"


class MonitoringTubeListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.MonitoringTubeSerializer
    queryset = gmw_models.MonitoringTube.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.MonitoringTubeFilter


class MonitoringTubeDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gmw_models.MonitoringTube.objects.all()
    serializer_class = serializers.MonitoringTubeSerializer
    lookup_field = "uuid"


class EventListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.EventSerializer
    queryset = gmw_models.Event.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.EventFilter


class EventDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gmw_models.Event.objects.all()
    serializer_class = serializers.EventSerializer
    lookup_field = "uuid"
