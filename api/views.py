import json

from rest_framework import status, generics
from django.contrib.auth.models import User
from rest_framework.response import Response
from . import tasks
from . import serializers
from . import models


class ImportTaskView(generics.ListAPIView):
    """
    This endpoint handles the import of data from the BRO.
    As input, it takes one of the four possible BRO Objects (GMN, GMW, GLD, FRD).
    It saves the imported data in the corresponding datamodel.
    The progress can be followed in the generated import task instance.

    **POST Parameters**

    `BRO object`:
        String (*required*) options: 'GMN', 'GMW', 'GLD', 'FRD'
    """

    serializer_class = serializers.ImportTaskSerializer
    queryset = models.ImportTask.objects.all()

    def get(self, request, *args, **kwargs):
        """List of all Import Tasks.
        """
        return self.list(request, *args, **kwargs)

    def post(self, request):
        """
        Initialize an import task by posting a BRO object.
        """

        serializer = serializers.ImportTaskSerializer(data=request.data)
        
        if serializer.is_valid():
            instance = serializer.save()
        
            # Collect the relevant data
            input_data = json.dumps(request.data)
            instance_uuid = instance.uuid

            user_profile = models.UserProfile.objects.get(user=request.user)
            organisation = user_profile.organisation
            organisation_uuid = organisation.uuid

            # Update the status of the new task
            instance.status = "PENDING"
            instance.organisation = organisation
            instance.save()

            # Start the celery task
            tasks.import_bro_data_task.delay(instance_uuid, input_data, organisation_uuid)
            
            # Handle the response
            url = f"http://localhost:8000/api/import-tasks/{instance.uuid}/"
            return Response({'message': f'Succesfully received the data. Check {url} for the status of the import task.'}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ImportTaskDetailView(generics.RetrieveAPIView):
    queryset = models.ImportTask.objects.all()
    serializer_class = serializers.ImportTaskSerializer
    lookup_field = 'uuid'

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)