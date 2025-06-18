from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import filters, serializers
from . import models as gld_models


class GLDListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.GLDSerializer
    queryset = gld_models.GLD.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GldFilter


class GLDIdsList(generics.ListAPIView):
    queryset = gld_models.GLD.objects.all()
    serializer_class = serializers.GLDIdsSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GldFilter
    filterset_fields = "__all__"


class GLDOverviewList(generics.ListAPIView):
    queryset = gld_models.GLD.objects.all()
    serializer_class = serializers.GLDOverviewSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GldFilter
    filterset_fields = "__all__"


class GLDDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gld_models.GLD.objects.all()
    serializer_class = serializers.GLDSerializer
    lookup_field = "uuid"


class ObservationListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.ObservationSerializer
    queryset = gld_models.Observation.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.ObservationFilter
    filterset_fields = "__all__"


class ObservationDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gld_models.Observation.objects.all()
    serializer_class = serializers.ObservationSerializer
    lookup_field = "uuid"
