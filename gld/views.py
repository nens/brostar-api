from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import filters, serializers
from . import models as gld_models


class GLDListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GLD objects for the user's organization.

    Returns:
        List of GLD objects ordered by creation date (descending).
    """

    serializer_class = serializers.GLDSerializer
    queryset = gld_models.GLD.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GldFilter


class GLDIdsList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GLD IDs for the user's organization.

    Returns:
        List of GLD IDs filtered by the specified filterset.
    """

    queryset = gld_models.GLD.objects.all()
    serializer_class = serializers.GLDIdsSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GldFilter
    filterset_fields = "__all__"


class GLDOverviewList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve an overview list of GLD objects for the user's organization.

    Returns:
        List of GLD overview data filtered by the specified filterset.
    """

    queryset = gld_models.GLD.objects.all()
    serializer_class = serializers.GLDOverviewSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GldFilter
    filterset_fields = "__all__"


class GLDDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single GLD object by UUID.

    Args:
        uuid (str): UUID of the GLD object.

    Returns:
        Detailed information about the specified GLD object.
    """

    queryset = gld_models.GLD.objects.all()
    serializer_class = serializers.GLDSerializer
    lookup_field = "uuid"


class ObservationListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of Observation objects for the user's organization.

    Returns:
        List of Observation objects ordered by creation date (descending).
    """

    serializer_class = serializers.ObservationSerializer
    queryset = gld_models.Observation.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.ObservationFilter
    filterset_fields = "__all__"


class ObservationDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single Observation object by UUID.

    Args:
        uuid (str): UUID of the Observation object.

    Returns:
        Detailed information about the specified Observation object.
    """

    queryset = gld_models.Observation.objects.all()
    serializer_class = serializers.ObservationSerializer
    lookup_field = "uuid"
