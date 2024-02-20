from rest_framework import generics, status
from rest_framework.response import Response
from . import serializers
from . import models


class GMWListView(generics.ListAPIView):
    serializer_class = serializers.GMWSerializer
    queryset = models.GMW.objects.all()

    def get(self, request, *args, **kwargs):
        """List of all GMWs."""
        return self.list(request, *args, **kwargs)


class GMWDetailView(generics.RetrieveAPIView):
    queryset = models.GMW.objects.all()
    serializer_class = serializers.GMWSerializer
    lookup_field = "uuid"

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MonitoringTubeListView(generics.ListAPIView):
    serializer_class = serializers.MonitoringTubeSerializer
    queryset = models.MonitoringTube.objects.all()

    def get(self, request, *args, **kwargs):
        """List of all MonitoringTubes."""
        return self.list(request, *args, **kwargs)


class MonitoringTubeDetailView(generics.RetrieveAPIView):
    queryset = models.MonitoringTube.objects.all()
    serializer_class = serializers.MonitoringTubeSerializer
    lookup_field = "uuid"

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
