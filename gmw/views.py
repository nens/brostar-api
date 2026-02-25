import logging

from django.core.cache import cache
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.response import Response

from api import mixins
from api.bro_upload.upload_datamodels import GMWConstruction
from gmn import models as gmn_models  # ADDED: Import GMN models

from . import filters, serializers
from . import models as gmw_models
from .xml_reader.xml_model import GMWXML

logger = logging.getLogger(__name__)


class GMWGeoJSONView(generics.ListAPIView):
    """Endpoint to serve all GMW data as GeoJSON FeatureCollection"""

    # REMOVED: Don't set queryset at class level, use get_queryset() instead
    serializer_class = serializers.GMWGeoJSONSerializer
    pagination_class = None  # CRITICAL: Disable pagination to return all data

    def get_queryset(self):
        user_org = self.request.user.userprofile.organisation

        return (
            gmw_models.GMW.objects.select_related("data_owner")
            .filter(data_owner=user_org)  # Filter by user's organization
            .prefetch_related(
                "tubes",  # Fetch tubes
                Prefetch(
                    "tubes__measuring_points",  # Then fetch measuring_points through tubes
                    queryset=gmn_models.Measuringpoint.objects.select_related("gmn"),
                ),
            )
        )

    def list(self, request, *args, **kwargs):
        """Override list to wrap in GeoJSON FeatureCollection and cache result"""

        # Check cache first
        cache_key = "gmw_geojson_all"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info("Returning cached GeoJSON data")
            return Response(cached_data)

        # Fetch and serialize data
        logger.info("Generating fresh GeoJSON data (cache miss)")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Wrap in GeoJSON FeatureCollection
        geojson = {
            "type": "FeatureCollection",
            "count": len(serializer.data),
            "features": serializer.data,
        }

        # Cache for 1 hour
        cache.set(cache_key, geojson, 60 * 60)
        logger.info(f"Cached {geojson['count']} GMW features")

        return Response(geojson)


class GMWAPIView(View):
    """
    API view that queries external API and returns JSON or XML
    based on Accept header or format parameter
    """

    def get(self, request, gmw_id):
        # Determine response format
        accept_header = request.headers.get("Accept", "")
        format_param = request.headers.get("Format", "").lower()
        # Check if XML is requested
        is_xml = "xml" in accept_header or format_param == "xml"

        # Query external API
        try:
            data = GMWXML(gmw_id, bro_url="https://publiek.broservices.nl/")
        except Exception as e:
            error_data = {"error": str(e), "gmw_id": gmw_id}
            if is_xml:
                return HttpResponse(
                    f"<error>{str(e)}</error>",
                    content_type="application/xml",
                    status=500,
                )
            return JsonResponse(error_data, status=500)

        # Return appropriate format
        if is_xml:
            response = HttpResponse(data.xml_content, content_type="application/xml")
            return response

        gmw_model = GMWConstruction(**data.gmw_construction)
        return JsonResponse(gmw_model.model_dump())


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
