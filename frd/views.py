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


class MeasurementConfigurationListView(
    mixins.UserOrganizationMixin, generics.ListAPIView
):
    """
    API view to retrieve a list of MeasurementConfiguration objects for the user's organization.

    Returns:
        list: List of MeasurementConfiguration objects ordered by creation date (descending).
    """

    serializer_class = serializers.MeasurementConfigurationSerializer
    queryset = frd_models.MeasurementConfiguration.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.MeasurementConfigurationFilter
    ordering = ["id"]


class MeasurementConfigurationDetailView(
    mixins.UserOrganizationMixin, generics.RetrieveAPIView
):
    """
    API view to retrieve the details of a single MeasurementConfiguration object by UUID.

    Args:
        uuid (str): UUID of the MeasurementConfiguration object.

    Returns:
        MeasurementConfiguration: Detailed information about the specified MeasurementConfiguration object.
    """

    queryset = frd_models.MeasurementConfiguration.objects.all()
    serializer_class = serializers.MeasurementConfigurationSerializer
    lookup_field = "uuid"


class GeoElectricMeasurementListView(
    mixins.UserOrganizationMixin, generics.ListAPIView
):
    """
    API view to retrieve a list of GeoElectricMeasurement objects for the user's organization.

    Returns:
        list: List of GeoElectricMeasurement objects ordered by creation date (descending).
    """

    serializer_class = serializers.GeoElectricMeasurementSerializer
    queryset = frd_models.GeoElectricMeasurement.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.MeasurementFilter
    ordering = ["id"]


class GeoElectricMeasurementDetailView(
    mixins.UserOrganizationMixin, generics.RetrieveAPIView
):
    """
    API view to retrieve the details of a single GeoElectricMeasurement object by UUID.

    Args:
        uuid (str): UUID of the GeoElectricMeasurement object.

    Returns:
        GeoElectricMeasurement: Detailed information about the specified GeoElectricMeasurement object.
    """

    queryset = frd_models.GeoElectricMeasurement.objects.all()
    serializer_class = serializers.GeoElectricMeasurementSerializer
    lookup_field = "uuid"


class GeoElectricMeasureListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GeoElectricMeasure objects for the user's organization.

    Returns:
        list: List of GeoElectricMeasure objects ordered by creation date (descending).
    """

    serializer_class = serializers.GeoElectricMeasureSerializer
    queryset = frd_models.GeoElectricMeasure.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GeoElectricMeasureFilter
    ordering = ["id"]


class GeoElectricMeasureDetailView(
    mixins.UserOrganizationMixin, generics.RetrieveAPIView
):
    """
    API view to retrieve the details of a single GeoElectricMeasure object by UUID.

    Args:
        uuid (str): UUID of the GeoElectricMeasure object.

    Returns:
        GeoElectricMeasure: Detailed information about the specified GeoElectricMeasure object.
    """

    queryset = frd_models.GeoElectricMeasure.objects.all()
    serializer_class = serializers.GeoElectricMeasureSerializer
    lookup_field = "uuid"
