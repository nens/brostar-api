import io
import logging
import os
import uuid
import zipfile
from typing import Any

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from pydantic import ValidationError
from rest_framework import generics, permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from api import filters, mixins, models, serializers, tasks
from api.bro_upload import utils
from api.bro_upload.object_upload import XMLGenerator
from api.bro_upload.upload_datamodels import (
    GARBulkUploadMetadata,
    GLDBulkUploadMetadata,
    GLDBulkUploadSourcedocumentData,
    GMNBulkUploadMetadata,
    UploadTaskMetadata,
)
from api.choices import registration_type_datamodel_mapping
from api.utils import drop_empty_strings, strip_whitespace
from brostar_api import __version__

logger = logging.getLogger("general")


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
            "individual-imports": reverse(
                "api:objectimporttask-list", request=request, format=format
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
            "events": reverse("api:gmw:event-list", request=request, format=format),
            "gars": reverse("api:gar:gar-list", request=request, format=format),
            "field-measurements": reverse(
                "api:gar:field-measurement-list", request=request, format=format
            ),
            "laboratory-researches": reverse(
                "api:gar:laboratory-research-list", request=request, format=format
            ),
            "analysis-processes": reverse(
                "api:gar:analysis-process-list", request=request, format=format
            ),
            "analyses": reverse(
                "api:gar:analysis-list", request=request, format=format
            ),
            "glds": reverse("api:gld:gld-list", request=request, format=format),
            "observations": reverse(
                "api:gld:observation-list", request=request, format=format
            ),
            "frds": reverse("api:frd:frd-list", request=request, format=format),
            "gufs": reverse("api:guf:guf-list", request=request, format=format),
            "gpds": reverse("api:gpd:gpd-list", request=request, format=format),
            "reports": reverse("api:gpd:report-list", request=request, format=format),
            "geo-electric-measurements": reverse(
                "api:frd:geo-electric-measurement-list", request=request, format=format
            ),
            "geo-electric-measures": reverse(
                "api:frd:geo-electric-measure-list", request=request, format=format
            ),
            "measurement-configurations": reverse(
                "api:frd:measurementconfiguration-list", request=request, format=format
            ),
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

    @extend_schema(responses={200: serializers.UserLoggedInSerializer})
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
    http_method_names = ["get", "head", "patch", "options"]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["uuid", "name", "kvk_number"]

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
        if user_profile.organisation:
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


class ObjectImportTaskViewSet(mixins.UserOrganizationMixin, viewsets.ModelViewSet):
    """Import a single BRO object by its BRO ID.

    POST to this endpoint to trigger an on-demand import of one object without
    running a full bulk import.  The resulting ``ObjectImportTask`` can be
    polled to follow the status.

    **POST Parameters**

    `bro_id`:
        String (*required*) e.g. ``"GMW000000000001"``.  The domain is
        derived automatically from the first three characters.

    `force`:
        Boolean (*optional*, default ``false``).  When ``true``, skips the
        PDOK freshness check and always re-imports the object.
    """

    model = models.ObjectImportTask
    serializer_class = serializers.ObjectImportTaskSerializer
    lookup_field = "uuid"
    queryset = models.ObjectImportTask.objects.all().order_by("-created")
    filter_backends = [DjangoFilterBackend]
    filterset_fields = "__all__"

    # Only allow create + read; no updates or deletes via this endpoint.
    http_method_names = ["get", "post", "head", "options"]

    def create(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        from api.tasks import import_object_task

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bro_id: str = serializer.validated_data["bro_id"].strip().upper()
        bro_domain = bro_id[:3]

        from api.bro_import.config import object_importer_mapping

        if bro_domain not in object_importer_mapping:
            return Response(
                {
                    "bro_id": f"Onbekend BRO domein '{bro_domain}'. Verwacht: {sorted(object_importer_mapping.keys())}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_profile = models.UserProfile.objects.get(user=request.user)
        serializer.validated_data["bro_id"] = bro_id
        serializer.validated_data["bro_domain"] = bro_domain
        serializer.validated_data["data_owner"] = user_profile.organisation
        serializer.validated_data["status"] = "PENDING"

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        # Dispatch the Celery task after the DB row is committed.
        import_object_task.delay(str(serializer.instance.uuid))

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
        raw_sourcedocument_data = serializer.validated_data["sourcedocument_data"]
        sourcedocument_data = strip_whitespace(
            drop_empty_strings(raw_sourcedocument_data)
        )

        validation_class = registration_type_datamodel_mapping.get(
            serializer.validated_data["registration_type"]
        )
        if validation_class:
            try:
                if (
                    serializer.validated_data["registration_type"] == "GLD_Addition"
                    or "GUF" in serializer.validated_data["registration_type"]
                ):
                    validated_sourcedocument_data = validation_class(
                        **sourcedocument_data
                    )
                    serializer.validated_data["sourcedocument_data"] = (
                        validated_sourcedocument_data.model_dump(by_alias=True)
                    )
                else:
                    validation_class(**sourcedocument_data)
                    serializer.validated_data["sourcedocument_data"] = (
                        sourcedocument_data
                    )
            except ValidationError as e:
                errors = utils.simplify_validation_errors(e.errors())
                return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)

        # Accessing the authenticated user's organization
        user_profile = models.UserProfile.objects.get(user=request.user)
        if not user_profile.organisation:
            return Response(
                {"detail": "No organisation linked to this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Always enforce the organisation from the user, pass as kwarg so DRF
        # merges it into validated_data after read-only field filtering.
        serializer.save(data_owner=user_profile.organisation)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Allow updates but always enforce the user's organisation as data_owner."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        user_profile = models.UserProfile.objects.get(user=request.user)
        if not user_profile.organisation:
            return Response(
                {"detail": "No organisation linked to this user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save(data_owner=user_profile.organisation)

        return Response(serializer.data, status=status.HTTP_200_OK)

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
        upload_task = models.UploadTask.objects.get(uuid=uuid)

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
                    "message": f"The upload task has already finished with status: {upload_task.status}. Check the detail for more info."
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
            errors = delivery_info["brondocuments"][0].get("errors", [])

            # Check restuls in FAILED
            if len(errors) > 0:
                upload_task.bro_errors = errors
                upload_task.log = "The delivery failed"
                upload_task.status = "FAILED"
                upload_task.save()

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
                    upload_task.status = "COMPLETED"
                    upload_task.log = f"Upload geslaagd: {upload_task.bro_id}"
                    upload_task.progress = 100.00
                    upload_task.save(
                        update_fields=["bro_id", "status", "log", "progress"]
                    )

                    data_owner.request_count += 1
                    data_owner.save(update_fields=["request_count"])

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

    @extend_schema(
        description="Returns the generated XML file for this upload task.",
        responses={(200, "application/xml"): OpenApiTypes.STR},
    )
    @action(detail=True, methods=["get"], url_path="read_xml")
    def read_xml(self, request: HttpRequest, uuid: str | None = None) -> HttpResponse:
        """Endpoint to show the generated XML file of this upload task, which is generated on the fly."""
        upload_task = models.UploadTask.objects.get(uuid=uuid)

        xml_generator = XMLGenerator(
            registration_type=upload_task.registration_type,
            request_type=upload_task.request_type,
            metadata=upload_task.metadata,
            sourcedocs_data=upload_task.sourcedocument_data,
        )

        xml_str = xml_generator.create_xml_file()

        return HttpResponse(xml_str, content_type="application/xml")


class UploadTaskOverviewList(mixins.UserOrganizationMixin, generics.ListAPIView):
    """
    API endpoint that provides a filtered, paginated list of upload tasks with summary information.

    This endpoint returns an overview of all upload tasks, supporting filtering via query parameters.
    The response uses a lightweight serializer for performance and summary display.

    **Query Parameters**:
        - Any field supported by the UploadTaskFilter (see filterset for details).

    **Returns**:
        - 200 OK: A paginated list of upload task overviews.
    """

    queryset = models.UploadTask.objects.all()
    serializer_class = serializers.UploadTaskOverviewSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = filters.UploadTaskFilter
    filterset_fields = "__all__"


class BulkUploadViewSet(mixins.UserOrganizationMixin, viewsets.ModelViewSet):
    """Endpoint that handles the bulk uploads of files and related data.

    This endpoint interfaces with the BulkUpload model and supports the following POST parameters:

    `bulk_upload_type`:
        str (*required*): Options: ['GAR', 'GLD', 'GMN']

    `metadata`:
        json (*optional*): Open json field that can be filled in with information that cannot be provided through the upload files

    `files`:
        file (*required*): Accepts one or more files in either Excel or CSV format.



        When the bulk_upload_type is GAR, these 2 files are required:
            - fieldwork_file
            - lab_file

        When the bulk_upload_type is GLD or GMN, this 1 file is required:
            - measurement_tvp_file

    """

    model = models.BulkUpload
    serializer_class = serializers.BulkUploadSerializer
    lookup_field = "uuid"
    queryset = models.BulkUpload.objects.all().order_by("-created")
    parser_classes = (MultiPartParser,)
    filter_backends = [DjangoFilterBackend]

    def _create_gar(self, serializer, data_owner, fieldwork_file, lab_file):
        # The BulkUpload instance is created here, because the uuid needs to be passed to the celery task.
        self.perform_create(serializer)
        bulk_upload_instance = serializer.instance

        # the files are saved, so that the uuid of those instances can be passed to the task
        if fieldwork_file is not None:
            fieldwork_upload_file_instance = models.UploadFile.objects.create(
                bulk_upload=bulk_upload_instance,
                data_owner=data_owner,
                file=fieldwork_file,
            )
            fieldwork_uuid = fieldwork_upload_file_instance.uuid
        else:
            fieldwork_uuid = None

        if lab_file is not None:
            lab_upload_file_instance = models.UploadFile.objects.create(
                bulk_upload=bulk_upload_instance,
                data_owner=data_owner,
                file=lab_file,
            )
            lab_uuid = lab_upload_file_instance.uuid
        else:
            lab_uuid = None

        # Start celery task
        tasks.gar_bulk_upload_task.delay(
            bulk_upload_instance.uuid,
            fieldwork_uuid,
            lab_uuid,
        )
        return serializer

    def _create_gld(self, serializer, data_owner, measurement_tvp_file):
        # The BulkUpload instance is created here, because the uuid needs to be passed to the celery task.
        self.perform_create(serializer)
        bulk_upload_instance = serializer.instance

        # the file is saved, so that the uuid of those instances can be passed to the task
        measurement_tvp_file_instance = models.UploadFile(
            bulk_upload=bulk_upload_instance,
            data_owner=data_owner,
            file=measurement_tvp_file,
        )
        measurement_tvp_file_instance.save()
        # Start celery task
        tasks.gld_bulk_upload_task.delay(
            bulk_upload_instance.uuid,
            measurement_tvp_file_instance.uuid,
        )

        return serializer

    def _create_gmn(self, serializer, data_owner, measurement_tvp_file):
        # The BulkUpload instance is created here, because the uuid needs to be passed to the celery task.
        self.perform_create(serializer)
        bulk_upload_instance = serializer.instance

        # the file is saved, so that the uuid of those instances can be passed to the task
        measurement_tvp_file_instance = models.UploadFile(
            bulk_upload=bulk_upload_instance,
            data_owner=data_owner,
            file=measurement_tvp_file,
        )
        measurement_tvp_file_instance.save()

        # Start celery task
        tasks.gmn_bulk_upload_task.delay(
            bulk_upload_instance.uuid,
            measurement_tvp_file_instance.uuid,
        )

        return serializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Fill up missing data
        user_profile = models.UserProfile.objects.get(user=request.user)
        data_owner = user_profile.organisation
        serializer.validated_data["data_owner"] = data_owner

        # Handle the request based on the bulk_upload_type
        if serializer.validated_data["bulk_upload_type"] == "GAR":
            # Check data with pydantic models:
            try:
                GARBulkUploadMetadata(**serializer.validated_data["metadata"])
            except ValidationError as e:
                errors = utils.simplify_validation_errors(e.errors())
                return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)

            # Read files
            fieldwork_file = request.FILES.get("fieldwork_file", None)
            lab_file = request.FILES.get("lab_file", None)
            if not (fieldwork_file or lab_file):
                return Response(
                    {
                        "error": "You are trying to initiate a GAR bulk upload process, but did not provide a fieldwork file or lab file."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            self._create_gar(serializer, data_owner, fieldwork_file, lab_file)

        elif serializer.validated_data["bulk_upload_type"] == "GLD":
            # Check data with pydantic models:
            try:
                GLDBulkUploadMetadata(**serializer.validated_data["metadata"])
                GLDBulkUploadSourcedocumentData(
                    **serializer.validated_data["sourcedocument_data"]
                )
            except ValidationError as e:
                errors = utils.simplify_validation_errors(e.errors())
                return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)

            # Read files
            measurement_tvp_file = request.FILES.get("measurement_tvp_file", None)
            if not measurement_tvp_file:
                return Response(
                    {
                        "error": "You are trying to initiate a GLD bulk upload process, but did provide a file."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            self._create_gld(serializer, data_owner, measurement_tvp_file)

        elif serializer.validated_data["bulk_upload_type"] == "GMN":
            # Check data with pydantic models:
            try:
                GMNBulkUploadMetadata(**serializer.validated_data["metadata"])
            except ValidationError as e:
                errors = utils.simplify_validation_errors(e.errors())
                return Response({"detail": errors}, status=status.HTTP_400_BAD_REQUEST)

            # Read files
            measurement_tvp_file = request.FILES.get("measurement_tvp_file", None)
            if not measurement_tvp_file:
                return Response(
                    {
                        "error": "You are trying to initiate a GLD bulk upload process, but did provide a file."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            self._create_gmn(serializer, data_owner, measurement_tvp_file)

        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class RawXMLUploadView(APIView):
    """Accept a single BRO XML file or a ZIP archive of BRO XML files and deliver
    each one directly to the BRO validation and delivery service, bypassing
    template generation and Pydantic sourcedocument validation.

    Each XML inside the upload becomes its own UploadTask.  Progress can be
    monitored via the standard ``/api/uploadtasks/{{uuid}}/`` and
    ``/api/uploadtasks/{{uuid}}/check_status/`` endpoints.

    **POST Parameters (multipart/form-data)**

    ``file`` (*required*)
        A single ``.xml`` file or a ``.zip`` archive containing ``.xml`` files.
        Maximum size: {zip} MB for a ZIP archive, {xml} MB for a single XML.
        A ZIP may contain at most {entries} XML files.

    ``project_number`` (*required*)
        BRO project number used for validation and delivery.
    """.format(
        zip=getattr(settings, "RAW_XML_MAX_ZIP_MB", 250),
        xml=getattr(settings, "RAW_XML_MAX_XML_MB", 50),
        entries=getattr(settings, "RAW_XML_MAX_ZIP_ENTRIES", 100),
    )

    parser_classes = [MultiPartParser]

    _ZIP_MAGIC = b"PK\x03\x04"

    # ------------------------------------------------------------------ helpers

    def _size_limit_mb(self, key: str, default: int) -> int:
        return int(getattr(settings, key, default))

    def _extract_xml_entries(
        self, file_bytes: bytes, original_name: str
    ) -> list[tuple[str, bytes]]:
        """Return a list of (safe_filename, xml_bytes) tuples.

        For a ZIP file every member is inspected; non-XML entries and unsafe
        filenames are silently skipped.  Oversized entries are rejected with a
        ``ValueError``.
        """
        max_xml_bytes = self._size_limit_mb("RAW_XML_MAX_XML_MB", 50) * 1024 * 1024
        max_entries = self._size_limit_mb("RAW_XML_MAX_ZIP_ENTRIES", 100)
        max_total_bytes = self._size_limit_mb("RAW_XML_MAX_ZIP_MB", 250) * 1024 * 1024

        if file_bytes[:4] == self._ZIP_MAGIC:
            entries: list[tuple[str, bytes]] = []
            cumulative = 0
            try:
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                    for info in zf.infolist():
                        safe_name = os.path.basename(info.filename)
                        # Reject path traversal and non-XML entries
                        if not safe_name or ".." in info.filename:
                            continue
                        if not safe_name.lower().endswith(".xml"):
                            continue
                        if len(entries) >= max_entries:
                            break
                        if info.file_size > max_xml_bytes:
                            raise ValueError(
                                f"Bestand '{safe_name}' overschrijdt de maximale bestandsgrootte "
                                f"van {max_xml_bytes // (1024 * 1024)} MB."
                            )
                        cumulative += info.file_size
                        if cumulative > max_total_bytes:
                            raise ValueError(
                                f"De totale gedecomprimeerde grootte van de ZIP overschrijdt "
                                f"{max_total_bytes // (1024 * 1024)} MB."
                            )
                        xml_bytes = zf.read(info.filename)
                        entries.append((safe_name, xml_bytes))
            except zipfile.BadZipFile as exc:
                raise ValueError(f"Ongeldig ZIP-bestand: {exc}") from exc
            return entries
        else:
            # Treat as a single XML file
            return [(original_name, file_bytes)]

    def _process_xml_entries(
        self,
        entries: list[tuple[str, bytes]],
        organisation: Any,
        project_number: str,
        bro_username: str,
        bro_password: str,
    ) -> tuple[list[dict], list[str]]:
        """Create an UploadTask and fire a Celery task for each valid XML entry.

        Returns (created, skipped) where each element of *created* is a dict
        summarising the new task and *skipped* lists filenames that could not
        be processed.
        """
        created: list[dict] = []
        skipped: list[str] = []

        for filename, xml_bytes in entries:
            try:
                xml_meta = utils.parse_raw_xml_metadata(xml_bytes)
            except ValueError as exc:
                logger.warning("Skipping '%s': %s", filename, exc)
                skipped.append(filename)
                continue

            try:
                xml_string = xml_bytes.decode("utf-8")
            except UnicodeDecodeError:
                logger.warning("Skipping '%s': not valid UTF-8", filename)
                skipped.append(filename)
                continue

            cache_key = f"raw_xml_{uuid.uuid4().hex}"
            cache.set(cache_key, xml_string, timeout=3600)

            upload_task = models.UploadTask.objects.create(
                data_owner=organisation,
                bro_domain=xml_meta["bro_domain"],
                project_number=project_number,
                registration_type=xml_meta["registration_type"],
                request_type=xml_meta["request_type"],
                metadata={"_is_raw_xml": True, "requestReference": str(uuid.uuid4())},
                sourcedocument_data={"filename": filename},
                status="PENDING",
            )

            tasks.validate_and_deliver_raw_xml_task.delay(
                str(upload_task.uuid),
                bro_username,
                bro_password,
                cache_key,
            )

            created.append(
                {
                    "uuid": str(upload_task.uuid),
                    "filename": filename,
                    "registration_type": xml_meta["registration_type"],
                    "request_type": xml_meta["request_type"],
                }
            )

        return created, skipped

    # ------------------------------------------------------------------ POST

    def _resolve_credentials(self, request: HttpRequest):
        """Return (organisation, bro_username, bro_password, error_response).

        *error_response* is non-None when the caller should return early.
        """
        user_profile = models.UserProfile.objects.get(user=request.user)
        organisation = user_profile.organisation
        if not organisation:
            return (
                None,
                None,
                None,
                Response(
                    {"detail": "No organisation linked to this user."},
                    status=status.HTTP_400_BAD_REQUEST,
                ),
            )
        bro_username = organisation.bro_user_token
        bro_password = organisation.bro_user_password
        if not bro_username or not bro_password:
            return (
                None,
                None,
                None,
                Response(
                    {"detail": "No BRO credentials configured for this organisation."},
                    status=status.HTTP_400_BAD_REQUEST,
                ),
            )
        return organisation, bro_username, bro_password, None

    def post(self, request: HttpRequest) -> HttpResponse:
        organisation, bro_username, bro_password, err = self._resolve_credentials(
            request
        )
        if err is not None:
            return err
        assert organisation is not None
        assert bro_username is not None
        assert bro_password is not None

        # --- project_number ---------------------------------------------------
        project_number = request.data.get("project_number", "").strip()
        if not project_number:
            return Response(
                {"detail": "project_number is verplicht."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- uploaded file ----------------------------------------------------
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"detail": "Geen bestand ontvangen. Gebruik het veld 'file'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        original_name = uploaded_file.name or "upload.xml"
        max_zip_bytes = self._size_limit_mb("RAW_XML_MAX_ZIP_MB", 250) * 1024 * 1024
        max_xml_bytes = self._size_limit_mb("RAW_XML_MAX_XML_MB", 50) * 1024 * 1024

        file_bytes = uploaded_file.read()

        # --- size check -------------------------------------------------------
        is_zip = file_bytes[:4] == self._ZIP_MAGIC
        size_limit = max_zip_bytes if is_zip else max_xml_bytes
        if len(file_bytes) > size_limit:
            limit_mb = size_limit // (1024 * 1024)
            return Response(
                {
                    "detail": f"Bestand is groter dan de maximaal toegestane {limit_mb} MB."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- detect file type by content, not Content-Type header -------------
        first_non_ws = file_bytes.lstrip()[:1]
        if not is_zip and first_non_ws not in (b"<", b"\xef"):  # XML or UTF-8 BOM
            return Response(
                {"detail": "Bestand moet een XML- of ZIP-bestand zijn."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- extract entries --------------------------------------------------
        try:
            entries = self._extract_xml_entries(file_bytes, original_name)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if not entries:
            return Response(
                {
                    "detail": "Geen geldige XML-bestanden gevonden in het geüploade bestand."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- process each XML -------------------------------------------------
        created, skipped = self._process_xml_entries(
            entries, organisation, project_number, bro_username, bro_password
        )

        if not created:
            return Response(
                {
                    "detail": "Geen geldig XML-bestanden verwerkt.",
                    "skipped": skipped,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data: dict = {"created": created}
        if skipped:
            response_data["skipped"] = skipped

        return Response(response_data, status=status.HTTP_202_ACCEPTED)
