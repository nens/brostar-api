from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import filters, serializers
from . import models as guf_models


class GUFListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GUF objects for the user's organization.

    Returns:
        list: List of GUF objects ordered by creation date (descending).
    """

    serializer_class = serializers.GUFSerializer
    queryset = guf_models.GUF.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GufFilter
    ordering = ["id"]


class GUFIdsList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GUF IDs for the user's organization.

    Returns:
        list: List of GUF IDs filtered by the specified filterset.
    """

    queryset = guf_models.GUF.objects.all()
    serializer_class = serializers.GUFIdsSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GufFilter
    ordering = ["id"]


class GUFDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single GUF object by UUID.

    Args:
        uuid (str): UUID of the GUF object.

    Returns:
        GUF: Detailed information about the specified GUF object.
    """

    queryset = guf_models.GUF.objects.all()
    serializer_class = serializers.GUFDetailSerializer
    lookup_field = "uuid"


# Design Installation Views
class DesignInstallationListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of Design Installation objects for the user's organization.

    Returns:
        list: List of Design Installation objects ordered by creation date (descending).
    """

    serializer_class = serializers.DesignInstallationSerializer
    queryset = guf_models.DesignInstallation.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    ordering = ["id"]


class DesignInstallationDetailView(
    mixins.UserOrganizationMixin, generics.RetrieveAPIView
):
    """
    API view to retrieve the details of a single Design Installation object by UUID.

    Args:
        uuid (str): UUID of the Design Installation object.

    Returns:
        DesignInstallation: Detailed information about the specified Design Installation object.
    """

    queryset = guf_models.DesignInstallation.objects.all()
    serializer_class = serializers.DesignInstallationSerializer
    lookup_field = "uuid"


# Design Loop Views
class DesignLoopListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of Design Loop objects for the user's organization.
    """

    serializer_class = serializers.DesignLoopSerializer
    queryset = guf_models.DesignLoop.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    ordering = ["id"]


class DesignLoopDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single Design Loop object by UUID.
    """

    queryset = guf_models.DesignLoop.objects.all()
    serializer_class = serializers.DesignLoopSerializer
    lookup_field = "uuid"


# Design Well Views
class DesignWellListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of Design Well objects for the user's organization.
    """

    serializer_class = serializers.DesignWellSerializer
    queryset = guf_models.DesignWell.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    ordering = ["id"]


class DesignWellDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single Design Well object by UUID.
    """

    queryset = guf_models.DesignWell.objects.all()
    serializer_class = serializers.DesignWellSerializer
    lookup_field = "uuid"


# Design Surface Infiltration Views
class DesignSurfaceInfiltrationListView(
    mixins.UserOrganizationMixin, generics.ListAPIView
):
    """
    API view to retrieve a list of Design Surface Infiltration objects for the user's organization.
    """

    serializer_class = serializers.DesignSurfaceInfiltrationSerializer
    queryset = guf_models.DesignSurfaceInfiltration.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    ordering = ["id"]


class DesignSurfaceInfiltrationDetailView(
    mixins.UserOrganizationMixin, generics.RetrieveAPIView
):
    """
    API view to retrieve the details of a single Design Surface Infiltration object by UUID.
    """

    queryset = guf_models.DesignSurfaceInfiltration.objects.all()
    serializer_class = serializers.DesignSurfaceInfiltrationSerializer
    lookup_field = "uuid"


# GUF Event Views
class GUFEventListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GUF Event objects for the user's organization.
    """

    serializer_class = serializers.GUFEventSerializer
    queryset = guf_models.GUFEvent.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    ordering = ["id"]


class GUFEventDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single GUF Event object by UUID.
    """

    queryset = guf_models.GUFEvent.objects.all()
    serializer_class = serializers.GUFEventSerializer
    lookup_field = "uuid"


# Energy Characteristics Views
class EnergyCharacteristicsListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of Energy Characteristics objects for the user's organization.
    """

    serializer_class = serializers.EnergyCharacteristicsSerializer
    queryset = guf_models.EnergyCharacteristics.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    ordering = ["id"]


class EnergyCharacteristicsDetailView(
    mixins.UserOrganizationMixin, generics.RetrieveAPIView
):
    """
    API view to retrieve the details of a single Energy Characteristics object by UUID.
    """

    queryset = guf_models.EnergyCharacteristics.objects.all()
    serializer_class = serializers.EnergyCharacteristicsSerializer
    lookup_field = "uuid"
