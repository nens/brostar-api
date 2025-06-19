from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import filters, serializers
from . import models as gmn_models


class GMNListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    Retrieve a list of GMN objects.

    Supports filtering via DjangoFilterBackend and GmnFilter.
    Results are ordered by creation date (descending).
    """

    serializer_class = serializers.GMNSerializer
    queryset = gmn_models.GMN.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GmnFilter


class GMNIdsList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    Retrieve a list of GMN object IDs.

    Supports filtering via DjangoFilterBackend and GmnFilter.
    """

    queryset = gmn_models.GMN.objects.all()
    serializer_class = serializers.GMNIdsSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GmnFilter


class GMNOverviewList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    Retrieve a list of GMN objects with overview serializer.

    Supports filtering via DjangoFilterBackend and GmnFilter.
    """

    queryset = gmn_models.GMN.objects.all()
    serializer_class = serializers.GMNOverviewSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GmnFilter


class GMNDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    Retrieve a single GMN object by UUID.

    Args:
        uuid (str): The UUID of the GMN object to retrieve.

    Returns:
        Detailed information about the GMN object.
    """

    queryset = gmn_models.GMN.objects.all()
    serializer_class = serializers.GMNSerializer
    lookup_field = "uuid"


class MeasuringpointListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    Retrieve a list of Measuringpoint objects.

    Supports filtering via DjangoFilterBackend and MeasuringPointFilter.
    Results are ordered by creation date (descending).
    """

    serializer_class = serializers.MeasuringpointSerializer
    queryset = gmn_models.Measuringpoint.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.MeasuringPointFilter


class MeasuringpointDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    Retrieve a single Measuringpoint object by UUID.
    """

    queryset = gmn_models.Measuringpoint.objects.all()
    serializer_class = serializers.MeasuringpointSerializer
    lookup_field = "uuid"


class EventListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    Retrieve a list of IntermediateEvent objects.

    Supports filtering via DjangoFilterBackend and IntermediateEventFilter.
    Results are ordered by creation date (descending).
    """

    serializer_class = serializers.IntermediateEventSerializer
    queryset = gmn_models.IntermediateEvent.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.IntermediateEventFilter


class EventDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    Retrieve a single IntermediateEvent object by UUID.
    """

    queryset = gmn_models.IntermediateEvent.objects.all()
    serializer_class = serializers.IntermediateEventSerializer
    lookup_field = "uuid"
