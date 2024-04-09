from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api import filters, mixins, models, serializers
from api.bro_upload import utils


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


class ImportTaskViewSet(mixins.UserOrganizationMixin, viewsets.ModelViewSet):
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

    model = models.ImportTask
    serializer_class = serializers.ImportTaskSerializer
    lookup_field = "uuid"
    queryset = models.ImportTask.objects.all().order_by("-created")
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Accessing the authenticated user's organization
        user_profile = models.UserProfile.objects.get(user=request.user)
        data_owner = user_profile.organisation
        serializer.validated_data["data_owner"] = data_owner
        serializer.validated_data["kvk_number"] = data_owner.kvk_number

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class UploadTaskViewSet(mixins.UserOrganizationMixin, viewsets.ModelViewSet):
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

    model = models.UploadTask
    serializer_class = serializers.UploadTaskSerializer
    lookup_field = "uuid"
    queryset = models.UploadTask.objects.all().order_by("-created")
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.UploadTaskFilter

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Accessing the authenticated user's organization
        user_profile = models.UserProfile.objects.get(user=request.user)
        data_owner = user_profile.organisation
        serializer.validated_data["data_owner"] = data_owner

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
    
    @action(detail=True, methods=['post'])
    def check_status(self, request, uuid=None):
        """Check the status of the upload task.
        
        **Returns**:

            - 202 when the task was stuck on PENDING. Start the task.

            - 303 when the task finished with a status of COMPLETED, FAILED, or PROCESSING

            - 200 when the task was UNFINISHED and successfully checked its status

            - 304 when the task was UNFINISHED, but remains UNFINISHED after a check with the BRO
         """
        upload_task = self.get_object()
        
        # Restart the task when its stuck on pending
        if upload_task.status == "PENDING":
            upload_task.save()
            return Response(
                {"message":"The task has been started after being stuck on PENDING"},
                status=status.HTTP_201_CREATED
            )
        
        # If task is still processing, return 303
        if upload_task.status == "PROCESSING":
            return Response(
                {"message":"The task is still running"},
                status=status.HTTP_303_SEE_OTHER
            )

        # If task was finished allready, return 303
        if upload_task.status in ["COMPLETED", "FAILED"]:
            return Response(
                {"message":f"The upload task has allready finished with status: {upload_task.status}. Check the detail for more info."},
                status=status.HTTP_303_SEE_OTHER
            )
        
        # If task failed, Check its status and return 
        if upload_task.status == "UNFINISHED":
            # Get relevant data to check status
            delivery_url = upload_task.bro_delivery_url
            user_profile = models.UserProfile.objects.get(user=request.user)
            data_owner = user_profile.organisation
            bro_username, bro_password = data_owner.bro_user_token, data_owner.bro_user_password
            delivery_info = utils.check_delivery_status(
                delivery_url, bro_username, bro_password
            )
            errors = delivery_info["brondocuments"][0]["errors"]

            # Check restuls in FAILED
            if errors:
                upload_task.bro_errors = errors
                upload_task.log = "The delivery failed"
                upload_task.status = "FAILED"
                return Response(
                {"message":"The upload failed. Check the detail page for more info."},
                status=status.HTTP_303_SEE_OTHER
            )

            else:
                delivery_status = delivery_info["status"]
                delivery_brondocument_status = delivery_info["brondocuments"][0]["status"]
                
                # Check results in FINISHED
                if (
                    delivery_status == "DOORGELEVERD"
                    and delivery_brondocument_status == "OPGENOMEN_LVBRO"
                ):
                    # Set BRO id to self to enable an import task based on the bro id. This keeps the data up2date in the api.
                    upload_task.bro_id = delivery_info["brondocuments"][0]["broId"]
                    upload_task.status == "FINISHED"
                    upload_task.save()

                    return Response(
                        {"message":"The upload was succesfull and the status is now FINISHED."},
                        status=status.HTTP_200_OK
                    )
                # Check remains UNFINISHED
                else:
                    return Response(
                        {"message":"The upload is still not completely handled in the BRO. Check the status later again."},
                        status=status.HTTP_304_NOT_MODIFIED
                    )
            