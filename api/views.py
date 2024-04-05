from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.reverse import reverse

from . import filters, mixins, models, serializers, tasks


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
            "users": reverse("api:user-list", request=request, format=format),
            "importtasks": reverse(
                "api:importtask-list", request=request, format=format
            ),
            "uploadtasks": reverse(
                "api:uploadtask-list", request=request, format=format
            ),
            "gmns": reverse("api:gmn:gmn-list", request=request, format=format),
            "measuringpoints": reverse(
                "api:gmn:measuringpoint-list", request=request, format=format
            ),
            "gmws": reverse("api:gmw:gmw-list", request=request, format=format),
            "monitoringtubes": reverse(
                "api:gmw:monitoringtube-list", request=request, format=format
            ),
        }
        return Response(data)


class UserViewSet(viewsets.ModelViewSet):
    model = User
    serializer_class = serializers.UserSerializer
    lookup_field = "pk"

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.filter(pk=user.pk)

        return queryset

    @action(
        detail=False,
        url_path="logged-in",
    )
    def logged_in(self, request):
        """Endpoint to check whether the use is logged in or not."""
        user = self.request.user
        if user.is_anonymous:
            return Response(
                {
                    "logged_in": False,
                    "login_url": reverse(
                        "drf-login-override",
                        kwargs=None,
                        request=request,
                        format=None,
                    ),
                    "logout_url": None,
                    "user_id": None,
                    "username": None,
                    "first_name": None,
                    "last_name": None,
                    "email": None,
                    "organisation": None,
                    "kvk": None,
                }
            )
        else:
            user_profile = models.UserProfile.objects.get(user=user)
            return Response(
                {
                    "logged_in": True,
                    "login_url": None,
                    "logout_url": reverse(
                        "drf-logout-override",
                        kwargs=None,
                        request=request,
                        format=None,
                    ),
                    "user_id": user.pk,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "organisation": user_profile.organisation.name,
                    "kvk": user_profile.organisation.kvk_number,
                }
            )


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

    queryset = models.ImportTask.objects.all().order_by("-created")
    serializer_class = serializers.ImportTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"

    def get(self, request, *args, **kwargs):
        """List of all Import Tasks."""
        return self.list(request, *args, **kwargs)

    @method_decorator(csrf_exempt)
    def post(self, request):
        """
        Initialize an import task by posting a BRO object.
        """

        serializer = serializers.ImportTaskSerializer(
            data=request.data, context={"request": request}
        )

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

            # Start the celery task
            tasks.import_bro_data_task.delay(import_task_instance_uuid)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

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

    It takes the registration type, request type, and the sourcedocument data as input.
    This API handles the transformation, validation, and delivery of the data.
    The status of this process can be followed in the generated upload task instance.

    **POST Parameters**

    `bro_domain`:
        String (*required*) options: 'GMN', 'GMW', 'GLD', 'FRD'

    `kvk_number`:
        string (*optional*) When not filled in, the kvk of the organization linked to the user is used.

    `project_number`:
        String (*optional*) When not filled in, the default project number is used. If that doesn't exist, the upload fails.

    `registration_type`:
        String (*required*)

    `request_type`:
        String (*required*) options: registration, replace, insert, move, delete. Some may not be possible for a given registration_type. Check out [the documentation for this endpoint](https://github.com/nens/bro-hub/blob/main/upload_examples.ipynb) for the possible combinations

    `metadata`:
        dict (*required*) see [the documentation for this endpoint](https://github.com/nens/bro-hub/blob/main/upload_examples.ipynb)

    `sourcedocument_data`:
        dict (*required*) see [the documentation for this endpoint](https://github.com/nens/bro-hub/blob/main/upload_examples.ipynb)
    """

    serializer_class = serializers.UploadTaskSerializer
    queryset = models.UploadTask.objects.all().order_by("-created")
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.UploadTaskFilter

    def get(self, request, *args, **kwargs):
        """List of all Upload Tasks."""
        return self.list(request, *args, **kwargs)

    @method_decorator(csrf_exempt)
    def post(self, request):
        """
        Initialize an upload task by posting the bro_domain, registration_type, request_type, and the sourcedocument_data
        """

        serializer = serializers.UploadTaskSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            upload_task_instance: models.UploadTask = serializer.save()

            # Accessing the authenticated user's username and token
            user_profile = models.UserProfile.objects.get(user=request.user)
            data_owner = user_profile.organisation
            username = data_owner.bro_user_token
            password = data_owner.bro_user_password

            # Update the instance of the new task
            upload_task_instance.status = "PENDING"
            upload_task_instance.data_owner = data_owner
            upload_task_instance.save()

            # Start the celery task
            tasks.upload_bro_data_task.delay(
                upload_task_instance.uuid, username, password
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

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
