from rest_framework import status, generics, views
from rest_framework.response import Response
from django.urls import reverse
from rest_framework.reverse import reverse as drf_reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from django.contrib.auth import logout
from django.shortcuts import redirect

from . import tasks
from . import serializers
from . import models
from . import mixins
from . import filters


class LogoutView(views.APIView):
    """
    Django 5 does not have GET logout route anymore, so Django Rest Framework UI can't log out.
    This is a workaround until Django Rest Framework implements POST logout.
    Can be removed after next djangorestframework release (and update).
    Details: https://github.com/encode/django-rest-framework/issues/9206
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        logout(request)
        return redirect("/api")


class APIOverview(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, format=None):
        data = {
            "api-token": drf_reverse(
                "token_obtain_pair", request=request, format=format
            ),
            "userprofile": drf_reverse(
                "api:userprofile-list", request=request, format=format
            ),
            "importtasks": drf_reverse(
                "api:importtask-list", request=request, format=format
            ),
            "uploadtasks": drf_reverse(
                "api:uploadtask-list", request=request, format=format
            ),
            "gmns": drf_reverse("api:gmn:gmn-list", request=request, format=format),
            "measuringpoints": drf_reverse(
                "api:gmn:measuringpoint-list", request=request, format=format
            ),
            "gmws": drf_reverse("api:gmw:gmw-list", request=request, format=format),
            "monitoringtubes": drf_reverse(
                "api:gmw:monitoringtube-list", request=request, format=format
            ),
        }
        return Response(data)


class UserProfileListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    serializer_class = serializers.UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return models.UserProfile.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = models.UserProfile.objects.all()
    serializer_class = serializers.UserProfileSerializer
    lookup_field = "uuid"
    permission_classes = [permissions.IsAuthenticated]

    # update makes sure only project number, token and password can be changed
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        data = request.data
        allowed_fields = {
            "default_project_number",
            "bro_user_token",
            "bro_user_password",
        }
        for key in data.keys():
            if key not in allowed_fields:
                return Response(
                    {"error": f"Cannot update field {key}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class ImportTaskListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    This endpoint handles the import of data from the BRO.
    As input, it takes one of the four possible BRO Objects (GMN, GMW, GLD, FRD).
    It saves the imported data in the corresponding datamodel.
    The progress can be followed in the generated import task instance.

    **POST Parameters**

    `bro_domain`:
        String (*required*) options: 'GMN', 'GMW', 'GLD', 'FRD'

    `kvk_number`:
        string (*optional*). When not filled in, the kvk of the organisation linked to the user is used.
    """

    serializer_class = serializers.ImportTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"

    def get_queryset(self):
        """List of all Import Tasks ordered by updated_at in descending order."""
        queryset = models.ImportTask.objects.all().order_by("-updated_at")
        return queryset

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
            import_task_instance_uuid = import_task_instance.uuid
            user_profile = models.UserProfile.objects.get(user=request.user)
            data_owner = user_profile.organisation

            # Update the instance of the new task
            import_task_instance.status = "PENDING"
            import_task_instance.data_owner = data_owner
            import_task_instance.kvk_number = (
                import_task_instance.kvk_number or data_owner.kvk_number
            )
            import_task_instance.save()

            if not import_task_instance.kvk_number:
                return Response(
                    {
                        "error": "No KvK found. Please set a kvk number under the Organisation you are linked to."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Start the celery task
            tasks.import_bro_data_task.delay(import_task_instance_uuid)

            # Get the dynamic URL using reverse
            url = reverse(
                "api:importtask-detail", kwargs={"uuid": import_task_instance.uuid}
            )
            full_url = request.build_absolute_uri(url)

            return Response(
                {
                    "message": f"Succesfully received the import taks request. Check {full_url} for the status of the import task."
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ImportTaskDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = models.ImportTask.objects.all()
    serializer_class = serializers.ImportTaskSerializer
    lookup_field = "uuid"

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UploadTaskListView(mixins.UserOrganizationMixin, generics.ListAPIView):
    """This endpoint handles the upload of data to the BRO.

    It takes the registration type, request type and the sourcedocument data as input.
    This API handles the transformation, validation and delivery of the data.
    The status of this proces can be followed in the generated upload task instance.

    **POST Parameters**

    `bro_domain`:
        String (*required*) options: 'GMN', 'GMW', 'GLD', 'FRD'

    `kvk_number`:
        string (*optional*) When not filled in, the kvk of the organisation linked to the user is used.

    `project_number`:
        String (*optional*) When not filled in, the default project number is used. If that doesnt exist, the upload fails.

    `registration_type`:
        String (*required*) available options are found in the docs

    `request_type`:
        String (*required*) options: registration, replace, insert, move, delete. Some may not be possible for a given registration_type. Check the docs for the possible combinations

    `metadata`:
        dict (*required*) check the docs

    `sourcedocument_data`:
        dict (*required*) check the docs

    """

    serializer_class = serializers.UploadTaskSerializer
    queryset = models.UploadTask.objects.all()

    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.UploadTaskFilter

    def get(self, request, *args, **kwargs):
        """List of all Upload Tasks."""
        return self.list(request, *args, **kwargs)

    def post(self, request):
        """
        Initialize an upload task by posting the bro_domain, registartion_type, request_type, and the sourcedocument_data
        """

        serializer = serializers.UploadTaskSerializer(data=request.data)

        if serializer.is_valid():
            upload_task_instance = serializer.save()

            # Accessing the authenticated user's username and token
            user_profile = models.UserProfile.objects.get(user=request.user)
            data_owner = user_profile.organisation
            username = user_profile.bro_user_token
            password = user_profile.bro_user_password

            # Update the instance of the new task
            upload_task_instance.status = "PENDING"
            upload_task_instance.data_owner = data_owner
            upload_task_instance.project_number = (
                upload_task_instance.project_number
                or user_profile.default_project_number
            )
            upload_task_instance.save()

            if not upload_task_instance.project_number:
                return Response(
                    {
                        "error": "No project number found. Set a default project number under your user profile, or add one to the POST request data."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Start the celery task
            tasks.upload_bro_data_task.delay(
                upload_task_instance.uuid, username, password
            )

            # Get the dynamic URL using reverse
            url = reverse(
                "api:uploadtask-detail", kwargs={"uuid": upload_task_instance.uuid}
            )
            full_url = request.build_absolute_uri(url)

            return Response(
                {
                    "message": f"Succesfully received the upload taks request. Check {full_url} for the status of the import task."
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UploadTaskDetailView(mixins.UserOrganizationMixin, generics.RetrieveAPIView):
    queryset = models.UploadTask.objects.all()
    serializer_class = serializers.UploadTaskSerializer
    lookup_field = "uuid"

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
