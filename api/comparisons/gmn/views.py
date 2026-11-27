import re

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api import models as api_models
from api.bro_upload.upload_datamodels import UploadTaskMetadata

from . import client
from .compare import Action, compare
from .serializers import GMNComparisonSerializer, today_nl
from .xml_reader import ParsedGMN, parse_gmn_response

GMN_ID = re.compile(r"GMN\d{12}")


def build_metadata(gmn: ParsedGMN, action: Action) -> dict:
    return UploadTaskMetadata(
        request_reference=(
            f"{gmn.bro_id}_{action.registration_type}_"
            f"{action.measuring_point_code}_{action.event_date.isoformat()}"
        ),
        delivery_accountable_party=gmn.delivery_accountable_party,
        bro_id=gmn.bro_id,
        quality_regime=gmn.quality_regime or "IMBRO",
    ).model_dump(by_alias=True, exclude_none=True)


@extend_schema(
    summary="Vergelijk een GMN met de BRO en maak uploadtaken voor de verschillen",
    description=(
        "Stuur het complete meetnet. Zonder confirm geeft dit endpoint de acties "
        "die nodig zijn (200) en maakt het niets aan. Met confirm=true maakt het "
        "een uploadtaak per actie (201): GMN_MeasuringPoint, GMN_TubeReference of "
        "GMN_MeasuringPointEndDate. Een actief meetpunt dat ontbreekt, krijgt een "
        "einddatum."
    ),
    request=GMNComparisonSerializer,
)
class GMNComparisonView(APIView):
    def post(self, request: Request, gmn_id: str) -> Response:
        if not GMN_ID.fullmatch(gmn_id):
            raise ValidationError(
                f"{gmn_id} is geen geldig GMN-ID, bijvoorbeeld GMN000000000703."
            )

        serializer = GMNComparisonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        organisation = self._get_organisation(request)
        gmn = parse_gmn_response(client.fetch_gmn_xml(gmn_id))

        actions, errors = compare(
            gmn,
            data["measuring_points"],
            default_event_date=data["event_date"],
            today=today_nl(),
        )
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if not data["confirm"] or not actions:
            return Response({"actions": [action.to_dict() for action in actions]})

        created = []
        for action in actions:
            upload_task = api_models.UploadTask.objects.create(
                data_owner=organisation,
                bro_domain="GMN",
                project_number=data["project_number"],
                registration_type=action.registration_type,
                request_type="registration",
                metadata=build_metadata(gmn, action),
                sourcedocument_data=action.sourcedocument(),
            )
            created.append({**action.to_dict(), "uuid": str(upload_task.uuid)})

        return Response({"actions": created}, status=status.HTTP_201_CREATED)

    def _get_organisation(self, request: Request) -> api_models.Organisation:
        profile = getattr(request.user, "userprofile", None)
        organisation = getattr(profile, "organisation", None)
        if not organisation:
            raise ValidationError(
                "Deze gebruiker is niet aan een organisatie gekoppeld."
            )
        return organisation
