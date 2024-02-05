import json

from rest_framework import status, generics
from django.contrib.auth.models import User
from rest_framework.response import Response
from django.urls import reverse

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
        """List of all Import Tasks."""
        return self.list(request, *args, **kwargs)

    def post(self, request):
        """
        Initialize an import task by posting a BRO object.
        """

        serializer = serializers.ImportTaskSerializer(data=request.data)

        if serializer.is_valid():
            import_task_instance = serializer.save()

            # Collect the relevant data
            bro_domain = request.data.get("bro_domain")
            import_task_instance_uuid = import_task_instance.uuid
            user_profile = models.UserProfile.objects.get(user=request.user)
            organisation = user_profile.organisation

            # Update the instance of the new task
            import_task_instance.status = "PENDING"
            import_task_instance.organisation = organisation
            import_task_instance.bro_domain = bro_domain
            import_task_instance.save()

            # Start the celery task
            tasks.import_bro_data_task.delay(import_task_instance_uuid)

            # Get the dynamic URL using reverse
            url = reverse(
                "api:import-task-detail", kwargs={"uuid": import_task_instance.uuid}
            )
            full_url = request.build_absolute_uri(url)

            return Response(
                {
                    "message": f"Succesfully received the import taks request. Check {full_url} for the status of the import task."
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ImportTaskDetailView(generics.RetrieveAPIView):
    queryset = models.ImportTask.objects.all()
    serializer_class = serializers.ImportTaskSerializer
    lookup_field = "uuid"

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
