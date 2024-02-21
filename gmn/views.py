from rest_framework import generics, status
from rest_framework.response import Response
from . import serializers
from . import models
from api import mixins
from django_filters.rest_framework import DjangoFilterBackend


class GMNListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.GMNSerializer
    queryset = models.GMN.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'    

    def get(self, request, *args, **kwargs):
        """List of all GMNs."""
        return self.list(request, *args, **kwargs)


class GMNDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = models.GMN.objects.all()
    serializer_class = serializers.GMNSerializer
    lookup_field = "uuid"

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MeasuringpointListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.MeasuringpointSerializer
    queryset = models.Measuringpoint.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = '__all__'

    def get(self, request, *args, **kwargs):
        """List of all Measuringpoints."""
        return self.list(request, *args, **kwargs)


class MeasuringpointDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = models.Measuringpoint.objects.all()
    serializer_class = serializers.MeasuringpointSerializer
    lookup_field = "uuid"

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
