from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from api import mixins

from . import models, serializers


class GARViewSet(mixins.UserOrganizationMixin, viewsets.ModelViewSet):
    model = models.GAR
    serializer_class = serializers.GARSerializer
    lookup_field = "uuid"
    queryset = models.GAR.objects.all().order_by("-created")
    filter_backends = [DjangoFilterBackend]
