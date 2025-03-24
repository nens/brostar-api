from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import filters, serializers
from . import models as gmn_models


class GMNListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.GMNSerializer
    queryset = gmn_models.GMN.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.GmnFilter
    filterset_fields = "__all__"


class GMNDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gmn_models.GMN.objects.all()
    serializer_class = serializers.GMNSerializer
    lookup_field = "uuid"


class MeasuringpointListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.MeasuringpointSerializer
    queryset = gmn_models.Measuringpoint.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.MeasuringPointFilter
    filterset_fields = "__all__"


class MeasuringpointDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gmn_models.Measuringpoint.objects.all()
    serializer_class = serializers.MeasuringpointSerializer
    lookup_field = "uuid"


class EventListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.IntermediateEventSerializer
    queryset = gmn_models.IntermediateEvent.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.IntermediateEventFilter
    filterset_fields = "__all__"


class EventDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gmn_models.IntermediateEvent.objects.all()
    serializer_class = serializers.IntermediateEventSerializer
    lookup_field = "uuid"
