from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import models as gld_models
from . import serializers


class GLDListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.GLDSerializer
    queryset = gld_models.GLD.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"


class GLDDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gld_models.GLD.objects.all()
    serializer_class = serializers.GLDSerializer
    lookup_field = "uuid"


class ObservationListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.ObservationSerializer
    queryset = gld_models.Observation.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"


class ObservationDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gld_models.Observation.objects.all()
    serializer_class = serializers.ObservationSerializer
    lookup_field = "uuid"
