from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import models as gar_models
from . import serializers


class GARViewSet(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GAR objects for the user's organization.

    Returns:
        list: List of GAR objects ordered by creation date (descending).
    """

    model = gar_models.GAR
    serializer_class = serializers.GARSerializer
    lookup_field = "uuid"
    queryset = gar_models.GAR.objects.all().order_by("-created")
    filter_backends = [DjangoFilterBackend]


class GARIdsList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GAR IDs for the user's organization.

    Returns:
        list: List of GAR IDs filtered by the specified filterset.
    """

    queryset = gar_models.GAR.objects.all()
    serializer_class = serializers.GARIdsSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"


class GARDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single GAR object by UUID.

    Args:
        uuid (str): UUID of the GAR object.

    Returns:
        GAR: Detailed information about the specified GAR object.
    """

    queryset = gar_models.GAR.objects.all()
    serializer_class = serializers.GARSerializer
    lookup_field = "uuid"
