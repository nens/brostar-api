from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import filters, serializers
from . import models as gar_models


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
    filterset_class = filters.GarFilter
    ordering = ["id"]


class GARIdsList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of GAR IDs for the user's organization.

    Returns:
        list: List of GAR IDs filtered by the specified filterset.
    """

    queryset = gar_models.GAR.objects.all()
    serializer_class = serializers.GARIdsSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GarFilter
    ordering = ["id"]


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


class FieldMeasurementListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of FieldMeasurement objects for the user's organization.

    Returns:
        list: List of FieldMeasurement objects ordered by creation date (descending).
    """

    model = gar_models.FieldMeasurement
    serializer_class = serializers.FieldMeasurementSerializer
    lookup_field = "uuid"
    queryset = gar_models.FieldMeasurement.objects.all().order_by("-created")
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.FieldMeasurementFilter
    ordering = ["id"]


class FieldMeasurementDetailView(
    mixins.UserOrganizationMixin, generics.RetrieveAPIView
):
    """
    API view to retrieve the details of a single FieldMeasurement object by UUID.

    Args:
        uuid (str): UUID of the FieldMeasurement object.

    Returns:
        FieldMeasurement: Detailed information about the specified FieldMeasurement object.
    """

    queryset = gar_models.FieldMeasurement.objects.all()
    serializer_class = serializers.FieldMeasurementSerializer
    lookup_field = "uuid"


class LaboratoryResearchListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of LaboratoryResearch objects for the user's organization.

    Returns:
        list: List of LaboratoryResearch objects ordered by creation date (descending).
    """

    model = gar_models.LaboratoryResearch
    serializer_class = serializers.LaboratoryResearchSerializer
    lookup_field = "uuid"
    queryset = gar_models.LaboratoryResearch.objects.all().order_by("-created")
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.LaboratoryResearchFilter
    ordering = ["id"]


class LaboratoryResearchDetailView(
    mixins.UserOrganizationMixin, generics.RetrieveAPIView
):
    """
    API view to retrieve the details of a single LaboratoryResearch object by UUID.

    Args:
        uuid (str): UUID of the LaboratoryResearch object.

    Returns:
        LaboratoryResearch: Detailed information about the specified LaboratoryResearch object.
    """

    queryset = gar_models.LaboratoryResearch.objects.all()
    serializer_class = serializers.LaboratoryResearchSerializer
    lookup_field = "uuid"


class AnalysisProcessListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of AnalysisProcess objects for the user's organization.

    Returns:
        list: List of AnalysisProcess objects ordered by creation date (descending).
    """

    model = gar_models.AnalysisProcess
    serializer_class = serializers.AnalysisProcessSerializer
    lookup_field = "uuid"
    queryset = gar_models.AnalysisProcess.objects.all().order_by("-created")
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.AnalysisProcessFilter
    ordering = ["id"]


class AnalysisProcessDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single AnalysisProcess object by UUID.

    Args:
        uuid (str): UUID of the AnalysisProcess object.

    Returns:
        AnalysisProcess: Detailed information about the specified AnalysisProcess object.
    """

    queryset = gar_models.AnalysisProcess.objects.all()
    serializer_class = serializers.AnalysisProcessSerializer
    lookup_field = "uuid"


class AnalysisListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API view to retrieve a list of Analysis objects for the user's organization.

    Returns:
        list: List of Analysis objects ordered by creation date (descending).
    """

    model = gar_models.Analysis
    serializer_class = serializers.AnalysisSerializer
    lookup_field = "uuid"
    queryset = gar_models.Analysis.objects.all().order_by("-created")
    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.AnalysisFilter
    ordering = ["id"]


class AnalysisDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    """
    API view to retrieve the details of a single Analysis object by UUID.

    Args:
        uuid (str): UUID of the Analysis object.

    Returns:
        Analysis: Detailed information about the specified Analysis object.
    """

    queryset = gar_models.Analysis.objects.all()
    serializer_class = serializers.AnalysisSerializer
    lookup_field = "uuid"
