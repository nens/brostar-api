from rest_framework import generics, status
from rest_framework.response import Response
from . import serializers
from . import models
from api import mixins
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions

class GMWListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.GMWSerializer
    queryset = models.GMW.objects.all()

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'

    def get(self, request, *args, **kwargs):
        """List of all GMWs."""
        return self.list(request, *args, **kwargs)


class GMWDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = models.GMW.objects.all()
    serializer_class = serializers.GMWSerializer
    lookup_field = "uuid"

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MonitoringTubeListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.MonitoringTubeSerializer
    queryset = models.MonitoringTube.objects.all()

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'

    def get(self, request, *args, **kwargs):
        """List of all MonitoringTubes."""
        return self.list(request, *args, **kwargs)


class MonitoringTubeDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = models.MonitoringTube.objects.all()
    serializer_class = serializers.MonitoringTubeSerializer
    lookup_field = "uuid"
    
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
