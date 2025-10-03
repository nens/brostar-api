from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import filters, serializers
from . import models as gmw_models


class GMWListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GMW objects.

    Supports filtering via DjangoFilterBackend and GmwFilter.
    Results are ordered by creation date (descending).
    """

    serializer_class = serializers.GMWSerializer
    queryset = gmw_models.GMW.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GmwFilter
    ordering = ["id"]


class GMWDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve a single GMW object by UUID.
    """

    queryset = gmw_models.GMW.objects.all()
    serializer_class = serializers.GMWSerializer
    lookup_field = "uuid"


class GMWOverviewList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GMW objects with overview serializer.

    Supports filtering via DjangoFilterBackend and GmwFilter.
    """

    queryset = gmw_models.GMW.objects.all()
    serializer_class = serializers.GMWOverviewSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GmwFilter
    ordering = ["id"]


class GMWIdsList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GMW object IDs.

    Supports filtering via DjangoFilterBackend and GmwFilter.
    """

    queryset = gmw_models.GMW.objects.all()
    serializer_class = serializers.GMWIdsSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GmwFilter
    ordering = ["id"]


class MonitoringTubeListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of MonitoringTube objects.

    Supports filtering via DjangoFilterBackend and MonitoringTubeFilter.
    Results are ordered by creation date (descending).
    """

    serializer_class = serializers.MonitoringTubeSerializer
    queryset = gmw_models.MonitoringTube.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.MonitoringTubeFilter
    ordering = ["id"]


class MonitoringTubeDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve a single MonitoringTube object by UUID.
    """

    queryset = gmw_models.MonitoringTube.objects.all()
    serializer_class = serializers.MonitoringTubeSerializer
    lookup_field = "uuid"


class EventListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of Event objects.

    Supports filtering via DjangoFilterBackend and EventFilter.
    Results are ordered by creation date (descending).
    """

    serializer_class = serializers.EventSerializer
    queryset = gmw_models.Event.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.EventFilter
    ordering = ["id"]


class EventDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve a single Event object by UUID.
    """

    queryset = gmw_models.Event.objects.all()
    serializer_class = serializers.EventSerializer
    lookup_field = "uuid"
