"""Views for the GLD correction endpoints.

Each view is thin: validate, fetch the current truth from the BRO, merge the
correction into it and create a GLD_Addition / replace UploadTask.
"""

import logging
from typing import Any

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api import models as api_models

from ..exceptions import CorrectionValidationError, ObservationNotFound
from ..kvk import resolve_investigator_kvk, wants_organisation_kvk
from . import client, timespan
from .builder import build_addition, build_metadata
from .merging import measurement_from_payload, merge_measurements, merge_procedure
from .serializers import (
    GLDMeasurementCorrectionSerializer,
    GLDProcedureCorrectionSerializer,
)
from .xml_reader import ParsedGLD, ParsedObservation, parse_gld_response

logger = logging.getLogger("general")


class BaseGLDCorrectionView(APIView):
    """Shared plumbing for the GLD correction endpoints."""

    serializer_class: Any = None
    changed_key = "changed"

    def post(self, request: Request, gld_id: str, observation_id: str) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        organisation = self._get_organisation(request)
        parsed, observation = self._fetch_observation(gld_id, observation_id)

        measurements, procedure, period, changed, log = self.apply_correction(
            parsed, observation, data, request
        )

        investigator_kvk, kvk_log = resolve_investigator_kvk(
            user=request.user,
            explicit_kvk=data.get("investigator_kvk"),
            use_organisation_kvk=wants_organisation_kvk(request, data),
            delivery_accountable_party=observation.investigator_kvk
            or parsed.delivery_accountable_party,
            fallback_label="principalInvestigator"
            if observation.investigator_kvk
            else "deliveryAccountableParty",
        )
        log.append(kvk_log)

        metadata = build_metadata(parsed, data["correction_reason"])
        addition = build_addition(
            observation=observation,
            procedure=procedure,
            measurements=measurements,
            investigator_kvk=investigator_kvk,
            begin_position=period[0],
            end_position=period[1],
            result_time=period[2],
        )

        upload_task = api_models.UploadTask.objects.create(
            data_owner=organisation,
            bro_domain="GLD",
            project_number=data["project_number"],
            registration_type="GLD_Addition",
            request_type="replace",
            metadata=metadata.model_dump(by_alias=True),
            sourcedocument_data=addition.model_dump(mode="json", by_alias=True),
        )

        return Response(
            {
                "uuid": str(upload_task.uuid),
                self.changed_key: changed,
                "log": "\n".join(log),
            },
            status=status.HTTP_201_CREATED,
        )

    # ------------------------------------------------------------------ helpers

    def _get_organisation(self, request: Request) -> api_models.Organisation:
        profile = getattr(request.user, "userprofile", None)
        organisation = getattr(profile, "organisation", None)
        if not organisation:
            raise CorrectionValidationError(
                "Deze gebruiker is niet aan een organisatie gekoppeld."
            )
        return organisation

    def _fetch_observation(
        self, gld_id: str, observation_id: str
    ) -> tuple[ParsedGLD, ParsedObservation]:
        xml_string = client.fetch_observation_xml(gld_id, observation_id)
        parsed = parse_gld_response(xml_string)

        observation = parsed.get_observation(observation_id)
        if observation is None:
            raise ObservationNotFound(gld_id, observation_id)

        return parsed, observation

    def apply_correction(
        self,
        parsed: ParsedGLD,
        observation: ParsedObservation,
        data: dict[str, Any],
        request: Request,
    ) -> tuple[list[Any], dict[str, Any], tuple[str, str, str | None], int, list[str]]:
        raise NotImplementedError


@extend_schema(
    summary="Corrigeer metingen binnen een bestaande GLD-observatie",
    description=(
        "Haalt de observatie op bij de publieke BRO-uitgifteservice, vervangt of "
        "voegt de meegegeven metingen toe en maakt een GLD_Addition (replace) "
        "UploadTask aan.\n\n"
        "Met de queryparameter `delta_t` (seconden) wordt een meting die binnen "
        "die marge valt als dezelfde meting beschouwd en overschreven."
    ),
    request=GLDMeasurementCorrectionSerializer,
)
class GLDMeasurementCorrectionView(BaseGLDCorrectionView):
    serializer_class = GLDMeasurementCorrectionSerializer
    changed_key = "measurements_changed"

    def _delta_t(self, request: Request) -> float:
        raw = request.query_params.get("delta_t", "0")
        try:
            delta_t = float(raw)
        except (TypeError, ValueError) as exc:
            raise CorrectionValidationError(
                f"delta_t moet een getal in seconden zijn, '{raw}' is dat niet."
            ) from exc

        if delta_t < 0:
            raise CorrectionValidationError("delta_t mag niet negatief zijn.")
        return delta_t

    def apply_correction(
        self,
        parsed: ParsedGLD,
        observation: ParsedObservation,
        data: dict[str, Any],
        request: Request,
    ) -> tuple[list[Any], dict[str, Any], tuple[str, str, str | None], int, list[str]]:
        delta_t = self._delta_t(request)
        incoming = [
            measurement_from_payload(payload) for payload in data["measurements"]
        ]

        merged, changed, log = merge_measurements(
            observation.measurements, incoming, delta_t
        )

        period = (
            observation.begin_position or "",
            observation.end_position or "",
            observation.result_time,
        )

        # Rule 5: only consult the other observations when a measurement falls
        # outside the current period of this observation.
        outside = timespan.times_outside_period(observation, merged)
        if outside:
            summaries = client.fetch_observation_summaries(parsed.bro_id or "")
            for measurement in outside:
                timespan.assert_best_fitting_observation(
                    observation, summaries, measurement
                )

            period = timespan.recalculate_period(merged)
            log.append(
                f"Observatieperiode bijgewerkt naar {period[0]} t/m {period[1]} "
                f"(resultTime {period[2]})."
            )

        return merged, observation.procedure(), period, changed, log


@extend_schema(
    summary="Corrigeer de procedure van een bestaande GLD-observatie",
    description=(
        "Haalt de observatie op bij de publieke BRO-uitgifteservice, past de "
        "meegegeven proceduregegevens aan en maakt een GLD_Addition (replace) "
        "UploadTask aan. De metingen blijven ongewijzigd."
    ),
    request=GLDProcedureCorrectionSerializer,
)
class GLDProcedureCorrectionView(BaseGLDCorrectionView):
    serializer_class = GLDProcedureCorrectionSerializer
    changed_key = "variables_changed"

    def apply_correction(
        self,
        parsed: ParsedGLD,
        observation: ParsedObservation,
        data: dict[str, Any],
        request: Request,
    ) -> tuple[list[Any], dict[str, Any], tuple[str, str, str | None], int, list[str]]:
        if observation.repeat_procedure:
            # CHECK: the BRO only delivers a reference (xlink:href) here, so the
            # original procedure values are unknown within this observation.
            raise CorrectionValidationError(
                f"Observatie {observation.observation_id} verwijst naar de procedure "
                f"van {observation.observation_process_id} en kan daarom niet los "
                "gecorrigeerd worden. Corrigeer de observatie waarin de procedure "
                "is vastgelegd."
            )

        merged, changed, log = merge_procedure(
            observation.procedure(), data["procedure"]
        )

        period = (
            observation.begin_position or "",
            observation.end_position or "",
            observation.result_time,
        )

        return observation.measurements, merged, period, changed, log
