from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import filters, serializers
from . import models as gpd_models


class GPDListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GPD objects for the user's organization.

    Returns:
        list: List of GPD objects ordered by creation date (descending).
    """

    serializer_class = serializers.GPDSerializer
    queryset = gpd_models.GPD.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GpdFilter
    ordering = ["id"]


class GPDIdsList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GPD IDs for the user's organization.

    Returns:
        list: List of GPD IDs filtered by the specified filterset.
    """

    queryset = gpd_models.GPD.objects.all()
    serializer_class = serializers.GPDIdsSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GpdFilter
    ordering = ["id"]


class GPDDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single GPD object by UUID.

    Args:
        uuid (str): UUID of the GPD object.

    Returns:
        GPD: Detailed information about the specified GPD object.
    """

    queryset = gpd_models.GPD.objects.all()
    serializer_class = serializers.GPDSerializer
    lookup_field = "uuid"


class ReportListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GPD reports for the user's organization.

    Returns:
        list: List of GPD reports ordered by creation date (descending).
    """

    serializer_class = serializers.ReportSerializer
    queryset = gpd_models.Report.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    ordering = ["id"]


class ReportDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single GPD report by UUID.

    Args:
        uuid (str): UUID of the GPD report.

    Returns:
        Report: Detailed information about the specified GPD report.
    """

    queryset = gpd_models.Report.objects.all()
    serializer_class = serializers.ReportSerializer
    lookup_field = "uuid"
