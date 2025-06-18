from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from api import mixins

from . import models as gar_models
from . import serializers


class GARViewSet(mixins.UserOrganizationMixin, generics.ListAPIView):
    model = gar_models.GAR
    serializer_class = serializers.GARSerializer
    lookup_field = "uuid"
    queryset = gar_models.GAR.objects.all().order_by("-created")
    filter_backends = [DjangoFilterBackend]


class GARIdsList(generics.ListAPIView):
    queryset = gar_models.GAR.objects.all()
    serializer_class = serializers.GARIdsSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"


class GARDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = gar_models.GAR.objects.all()
    serializer_class = serializers.GARSerializer
    lookup_field = "uuid"
