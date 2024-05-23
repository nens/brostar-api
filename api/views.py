from typing import Any

from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from pydantic import ValidationError
from rest_framework import permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from api import filters, mixins, models, serializers, tasks
from api.bro_upload import utils
from api.bro_upload.upload_datamodels import GARBulkUploadMetadata, UploadTaskMetadata
from api.choices import registration_type_datamodel_mapping
from brostar_api import __version__


class LogoutView(views.APIView):
    """
    Django 5 does not have GET logout route anymore, so Django Rest Framework UI can't log out.
    This is a workaround until Django Rest Framework implements POST logout.
    Can be removed after next djangorestframework release (and update).
    Details: https://github.com/encode/django-rest-framework/issues/9206
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request: HttpRequest) -> HttpResponse:
        logout(request)
        return redirect("/api")


class APIOverview(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request: HttpRequest, format: Any = None) -> HttpResponse:
        data = {
            "users": reverse("api:user-list", request=request, format=format),
            "organisations": reverse(
                "api:organisation-list", request=request, format=format
            ),
            "importtasks": reverse(
                "api:importtask-list", request=request, format=format
            ),
            "uploadtasks": reverse(
                "api:uploadtask-list", request=request, format=format
            ),
            "bulk-uploads": reverse(
                "api:bulkupload-list", request=request, format=format
            ),
            "gmns": reverse("api:gmn:gmn-list", request=request, format=format),
            "measuringpoints": reverse(
                "api:gmn:measuringpoint-list", request=request, format=format
            ),
            "gmws": reverse("api:gmw:gmw-list", request=request, format=format),
            "monitoringtubes": reverse(
                "api:gmw:monitoringtube-list", request=request, format=format
            ),
            "gars": reverse("api:gar:gar-list", request=request, format=format),
        }
        return Response(data)


APIOverview.__doc__ = f"**BROstar version**: *{__version__}*"


class LocalHostRedirectView(APIView):
    """
    View that redirects user to localhost:4200.
    Is used for local frontend development on the stagin environment.
    """

    def get(
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> HttpResponseRedirect:
        return HttpResponseRedirect("http://localhost:4200")


class UserViewSet(viewsets.ModelViewSet):
    model = User
    serializer_class = serializers.UserSerializer
    lookup_field = "pk"

    permission_classes = []

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        queryset = User.objects.filter(pk=user.pk)

        return queryset

    @swagger_auto_schema(
        responses={200: serializers.UserLoggedInSerializer()},
    )
    @action(
        detail=False,
        url_path="logged-in",
    )
    def logged_in(self, request: HttpRequest) -> Response:
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
                    "organisation_url": None,
                    "kvk": None,
                    "organisation_current_request_count": None,
                    "bro_credentials_set": None,
                }
            )
        else:
            user_profile = models.UserProfile.objects.get(user=user)
            organisation = user_profile.organisation
            organisation_url = reverse(
                "api:organisation-list",
                kwargs=None,
                request=request,
                format=None,
            )
            bro_credentials_set = (
                True
                if organisation.bro_user_password and organisation.bro_user_token
                else False
            )

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
                    "organisation": organisation.name,
                    "organisation_url": f"{organisation_url}{organisation.uuid}",
                    "kvk": user_profile.organisation.kvk_number,
                    "organisation_current_request_count": organisation.request_count,
                    "bro_credentials_set": bro_credentials_set,
                }
            )


class OrganisationViewSet(viewsets.ModelViewSet):
    model = models.Organisation
    serializer_class = serializers.OrganisationSerializer
    lookup_field = "uuid"
    queryset = models.Organisation.objects.all().order_by("name")

    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"

    def update(self, request, *args, **kwargs):
        # validate that the user requests the change for own organisation
        user = request.user
        user_profile = models.UserProfile.objects.get(user=user)
        user_organisation = user_profile.organisation

        if self.get_object() != user_organisation:
            return Response(
                {"message": "Please change the credentials of your own organisation"},
                status=status.HTTP_403_FORBIDDEN,
            )

        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Check if request data contains credentials
        if "bro_user_token" in request.data or "bro_user_password" in request.data:
            credential_serializer = serializers.OrganisationCredentialSerializer(
                instance, data=request.data, partial=partial
            )
            credential_serializer.is_valid(raise_exception=True)
            credential_serializer.save()

        # Update the rest of the data
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {"message": "BRO credentials updated successfully"},
            status=status.HTTP_200_OK,
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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"

    def create(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Accessing the authenticated user's organization
        user_profile = models.UserProfile.objects.get(user=request.user)
        data_owner = user_profile.organisation
        serializer.validated_data["data_owner"] = data_owner

        kvk_number = serializer.validated_data.get("kvk_number")
        if not kvk_number:
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
        String (*required*) options: 'GMN', 'GMW', 'GLD', 'FRD', 'GAR'

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

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.UploadTaskFilter

    def create(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Validate the metadata input
        try:
            UploadTaskMetadata(**serializer.validated_data["metadata"])
        except ValidationError as e:
            errors = utils.simplify_validation_errors(e.errors())
            return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the sourcedocument_data input
        validation_class = registration_type_datamodel_mapping.get(
            serializer.validated_data["registration_type"]
        )

        try:
            validation_class(**serializer.validated_data["sourcedocument_data"])
        except ValidationError as e:
            errors = utils.simplify_validation_errors(e.errors())
            return Response({"detail": e.errors()}, status=status.HTTP_400_BAD_REQUEST)

        # Accessing the authenticated user's organization
        user_profile = models.UserProfile.objects.get(user=request.user)
        data_owner = user_profile.organisation
        serializer.validated_data["data_owner"] = data_owner

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=True, methods=["post"])
    def check_status(
        self, request: HttpRequest, uuid: str | None = None
    ) -> HttpResponse:
        """Check the status of the upload task.

        **Returns**:
            - 200 when the task was UNFINISHED and successfully checked its status

            - 202 when the task was stuck on PENDING. Start the task.

            - 303 when the task finished with a status of COMPLETED or FAILED

            - 303 when the task was still running

            - 304 when the task was UNFINISHED, but remains UNFINISHED after a check with the BRO
        """
        upload_task = self.get_object()

        # Restart the task when its stuck on pending
        if upload_task.status == "PENDING":
            upload_task.save()
            return Response(
                {"message": "The task has been started after being stuck on PENDING"},
                status=status.HTTP_201_CREATED,
            )

        # If task is still processing, return 303
        if upload_task.status == "PROCESSING":
            return Response(
                {"message": "The task is still running"},
                status=status.HTTP_303_SEE_OTHER,
            )

        # If task was finished allready, return 303
        if upload_task.status in ["COMPLETED", "FAILED"]:
            return Response(
                {
                    "message": f"The upload task has allready finished with status: {upload_task.status}. Check the detail for more info."
                },
                status=status.HTTP_303_SEE_OTHER,
            )

        # If task failed, Check its status and return
        if upload_task.status == "UNFINISHED":
            # Get relevant data to check status
            delivery_url = upload_task.bro_delivery_url
            user_profile = models.UserProfile.objects.get(user=request.user)
            data_owner = user_profile.organisation
            bro_username, bro_password = (
                data_owner.bro_user_token,
                data_owner.bro_user_password,
            )
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
                    {
                        "message": "The upload failed. Check the detail page for more info."
                    },
                    status=status.HTTP_303_SEE_OTHER,
                )

            else:
                delivery_status = delivery_info["status"]
                delivery_brondocument_status = delivery_info["brondocuments"][0][
                    "status"
                ]

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
                        {
                            "message": "The upload was succesfull and the status is now FINISHED."
                        },
                        status=status.HTTP_200_OK,
                    )
                # Check remains UNFINISHED
                else:
                    return Response(
                        {
                            "message": "The upload is still not completely handled in the BRO. Check the status later again."
                        },
                        status=status.HTTP_304_NOT_MODIFIED,
                    )


class BulkUploadViewSet(mixins.UserOrganizationMixin, viewsets.ModelViewSet):
    """Endpoint that handles the bulk uploads of files and related data.

    This endpoint interfaces with the BulkUpload model and supports the following POST parameters:

    `bulk_upload_type`:
        str (*required*): Options: 'GAR'

    `metadata`:
        json (*optional*): Open json field that can be filled in with information that cannot be provided through the upload files

    `files`:
        file (*required*): Accepts one or more files in either Excel or CSV format.



        When the bulk_upload_type is GAR, these 2 files are required:
            - fieldwork_file
            - lab_file

    """

    model = models.BulkUpload
    serializer_class = serializers.BulkUploadSerializer
    lookup_field = "uuid"
    queryset = models.BulkUpload.objects.all().order_by("-created")
    parser_classes = (MultiPartParser,)
    filter_backends = [DjangoFilterBackend]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "fieldwork_file", openapi.IN_FORM, type=openapi.TYPE_FILE
            ),
            openapi.Parameter("lab_file", openapi.IN_FORM, type=openapi.TYPE_FILE),
        ]
    )
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Fill up missing data
        user_profile = models.UserProfile.objects.get(user=request.user)
        data_owner = user_profile.organisation
        serializer.validated_data["data_owner"] = data_owner

        # Handle the request based on the bulk_upload_type
        if serializer.validated_data["bulk_upload_type"] == "GAR":
            try:
                # Check data with pydantic models:
                try:
                    GARBulkUploadMetadata(**serializer.validated_data["metadata"])
                except ValidationError as e:
                    errors = utils.simplify_validation_errors(e.errors())
                    return Response(
                        {"detail": errors}, status=status.HTTP_400_BAD_REQUEST
                    )

                # Read files
                fieldwork_file = request.FILES.get("fieldwork_file", None)
                lab_file = request.FILES.get("lab_file", None)

                if fieldwork_file and lab_file:
                    # The BulkUpload instance is created here, because the uuid needs to be passed to the celery task.
                    self.perform_create(serializer)
                    bulk_upload_instance = serializer.instance

                    # the files are saved, so that the uuid of those instances can be passed to the task
                    fieldwork_upload_file_instance = models.UploadFile(
                        bulk_upload=bulk_upload_instance,
                        data_owner=data_owner,
                        file=fieldwork_file,
                    )
                    fieldwork_upload_file_instance.save()

                    lab_upload_file_instance = models.UploadFile(
                        bulk_upload=bulk_upload_instance,
                        data_owner=data_owner,
                        file=lab_file,
                    )
                    lab_upload_file_instance.save()

                    # Fetch users bro credentials
                    bro_username = data_owner.bro_user_token
                    bro_password = data_owner.bro_user_password

                    # Start celery task
                    tasks.gar_bulk_upload_task.delay(
                        bulk_upload_instance.uuid,
                        fieldwork_upload_file_instance.uuid,
                        lab_upload_file_instance.uuid,
                        bro_username,
                        bro_password,
                    )
                else:
                    return Response(
                        {
                            "error": "You are trying to initiate a GAR bulk upload process, but did not provide a combination of a fieldwork and lab analysis file."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
