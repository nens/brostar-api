from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import models as frd_models
from . import serializers


class FRDListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.FRDSerializer
    queryset = frd_models.FRD.objects.all().order_by("-created")

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"


class FRDIdsList(generics.ListAPIView):
    queryset = frd_models.FRD.objects.all()
    serializer_class = serializers.FRDIdsSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"


class FRDDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = frd_models.FRD.objects.all()
    serializer_class = serializers.FRDSerializer
    lookup_field = "uuid"
