from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import filters, serializers
from . import models as frd_models


class FRDListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of FRD objects for the user's organization.

    Returns:
        list: List of FRD objects ordered by creation date (descending).
    """

    serializer_class = serializers.FRDSerializer
    queryset = frd_models.FRD.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.FrdFilter
    ordering = ["id"]


class FRDIdsList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of FRD IDs for the user's organization.

    Returns:
        list: List of FRD IDs filtered by the specified filterset.
    """

    queryset = frd_models.FRD.objects.all()
    serializer_class = serializers.FRDIdsSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.FrdFilter
    ordering = ["id"]


class FRDDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single FRD object by UUID.

    Args:
        uuid (str): UUID of the FRD object.

    Returns:
        FRD: Detailed information about the specified FRD object.
    """

    queryset = frd_models.FRD.objects.all()
    serializer_class = serializers.FRDSerializer
    lookup_field = "uuid"
