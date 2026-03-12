import logging
import time

from django.core.cache import cache
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from api import mixins
from api.bro_upload.upload_datamodels import GMWConstruction
from gmn import models as gmn_models  # ADDED: Import GMN models

from . import filters, serializers
from . import models as gmw_models
from .xml_reader.xml_model import GMWXML

logger = logging.getLogger(__name__)


class GMWGeoJSONView(APIView):
    """Endpoint to serve all GMW data as GeoJSON FeatureCollection"""

    @swagger_auto_schema(
        operation_description="Get all GMW data as a GeoJSON FeatureCollection",
        responses={
            200: openapi.Response(
                description="GeoJSON FeatureCollection",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "type": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="GeoJSON type",
                            enum=["FeatureCollection"],
                        ),
                        "count": openapi.Schema(
                            type=openapi.TYPE_INTEGER, description="Number of features"
                        ),
                        "features": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description="Array of GeoJSON Features",
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "type": openapi.Schema(
                                        type=openapi.TYPE_STRING, enum=["Feature"]
                                    ),
                                    "id": openapi.Schema(
                                        type=openapi.TYPE_STRING, format="uuid"
                                    ),
                                    "geometry": openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "type": openapi.Schema(
                                                type=openapi.TYPE_STRING, enum=["Point"]
                                            ),
                                            "coordinates": openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(
                                                    type=openapi.TYPE_NUMBER
                                                ),
                                                description="[longitude, latitude]",
                                                min_items=2,
                                                max_items=2,
                                            ),
                                        },
                                        required=["type", "coordinates"],
                                    ),
                                    "properties": openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "uuid": openapi.Schema(
                                                type=openapi.TYPE_STRING, format="uuid"
                                            ),
                                            "bro_id": openapi.Schema(
                                                type=openapi.TYPE_STRING, max_length=18
                                            ),
                                            "linked_gmns": openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(
                                                    type=openapi.TYPE_STRING
                                                ),
                                            ),
                                            "nitg_code": openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                x_nullable=True,
                                            ),
                                            "well_construction_date": openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                x_nullable=True,
                                            ),
                                            "nr_of_monitoring_tubes": openapi.Schema(
                                                type=openapi.TYPE_INTEGER
                                            ),
                                            "quality_regime": openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                x_nullable=True,
                                            ),
                                            "removed": openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                x_nullable=True,
                                            ),
                                            "tubes": openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        "uuid": openapi.Schema(
                                                            type=openapi.TYPE_STRING,
                                                            format="uuid",
                                                        ),
                                                        "tube_number": openapi.Schema(
                                                            type=openapi.TYPE_STRING,
                                                            x_nullable=True,
                                                        ),
                                                        "tube_status": openapi.Schema(
                                                            type=openapi.TYPE_STRING,
                                                            x_nullable=True,
                                                        ),
                                                    },
                                                ),
                                            ),
                                        },
                                    ),
                                },
                                required=["type", "id", "geometry", "properties"],
                            ),
                        ),
                    },
                    required=["type", "count", "features"],
                ),
                examples={
                    "application/json": {
                        "type": "FeatureCollection",
                        "count": 2,
                        "features": [
                            {
                                "type": "Feature",
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [5.123, 52.456],
                                },
                                "properties": {
                                    "uuid": "123e4567-e89b-12d3-a456-426614174000",
                                    "bro_id": "GMW000000001234",
                                    "linked_gmns": [
                                        "456e7890-e89b-12d3-a456-426614174000"
                                    ],
                                    "nitg_code": "B25E0123",
                                    "well_construction_date": "2020-01-15",
                                    "nr_of_monitoring_tubes": 3,
                                    "quality_regime": "IMBRO",
                                    "removed": None,
                                    "tubes": [
                                        {
                                            "uuid": "789e0123-e89b-12d3-a456-426614174000",
                                            "tube_number": "1",
                                            "tube_status": "active",
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                },
            )
        },
    )
    def get(self, request) -> Response:
        """
        Returns GeoJSON FeatureCollection with structure:
        {
            "type": "FeatureCollection",
            "count": int,
            "features": GMWGeoJSON[]
        }
        """
        user_org = request.user.userprofile.organisation

        # Check cache first
        cache_key = f"gmw_geojson_{user_org.uuid}"
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.info(f"✅ CACHE HIT - Returning cached data for org {user_org.uuid}")
            return Response(cached_data)

        # Cache miss - generate fresh data
        logger.info(f"❌ CACHE MISS - Generating fresh data for org {user_org.uuid}")
        start_time = time.time()

        # Build queryset
        queryset = (
            gmw_models.GMW.objects.select_related("data_owner")
            .filter(data_owner=user_org)
            .prefetch_related(
                "tubes",
                Prefetch(
                    "tubes__measuring_points",
                    queryset=gmn_models.Measuringpoint.objects.select_related("gmn"),
                ),
            )
        )

        # Serialize data
        serializer = serializers.GMWGeoJSONSerializer(queryset, many=True)

        # Wrap in GeoJSON FeatureCollection
        geojson = {
            "type": "FeatureCollection",
            "count": len(serializer.data),
            "features": serializer.data,
        }

        generation_time = time.time() - start_time
        logger.info(f"Generated {geojson['count']} features in {generation_time:.2f}s")

        # Cache for 1 hour
        cache.set(cache_key, geojson, 60 * 60)
        logger.info(f"✅ Cached data for org {user_org.uuid}")

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
