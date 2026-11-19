"""Views for the GLD correction endpoints.

Each view is thin: validate, fetch the current truth from the BRO, merge the
correction into it and create a GLD_Addition / replace UploadTask.
"""

import logging
import uuid
from typing import Any

from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api import models as api_models
from api.bro_upload.upload_datamodels import UploadTaskMetadata

from ..exceptions import CorrectionValidationError, ObservationNotFound
from ..kvk import resolve_investigator_kvk, wants_organisation_kvk
from . import client, timespan
from .builder import build_addition, build_metadata
from .merging import measurement_from_payload, merge_measurements, merge_procedure
from .registration import (
    build_segment_addition,
    fetch_tube_geometry,
    split_measurements,
)
from .serializers import (
    GLDMeasurementCorrectionSerializer,
    GLDProcedureCorrectionSerializer,
    GLDRegistrationSerializer,
)
from .validation import (
    DEFAULT_FLATLINE_SIGMA_MULTIPLIER,
    DEFAULT_PHYSICAL_TOLERANCE,
    DEFAULT_RULES,
    DEFAULT_SPIKE_SIGMA_MULTIPLIER,
    ValidationSettings,
    validate_measurements,
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
        "UploadTask aan. Metingen worden uitsluitend gematcht op hetzelfde "
        "genormaliseerde tijdstip."
    ),
    request=GLDMeasurementCorrectionSerializer,
)
class GLDMeasurementCorrectionView(BaseGLDCorrectionView):
    serializer_class = GLDMeasurementCorrectionSerializer
    changed_key = "measurements_changed"

    def apply_correction(
        self,
        parsed: ParsedGLD,
        observation: ParsedObservation,
        data: dict[str, Any],
        request: Request,
    ) -> tuple[list[Any], dict[str, Any], tuple[str, str, str | None], int, list[str]]:
        incoming = [
            measurement_from_payload(payload) for payload in data["measurements"]
        ]

        merged, changed, log = merge_measurements(observation.measurements, incoming)

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


@extend_schema(
    summary="Registreer een GLD_Addition op basis van metingen",
    description=(
        "Valideert de metingen en maakt een aparte GLD_Addition UploadTask voor "
        "elk aaneengesloten meetsegment. De standaardregels zijn flatline "
        "(vijf opeenvolgende lage delta's, standaard 0.1 standaarddeviatie), "
        "spike (standaard 3 standaarddeviaties), onder de tube-top en boven de "
        "tube-bottom (beide met een tolerantie van 0.1 m). De sensorhoogteregel "
        "is opt-in en vereist validation_options.sensor_height. Regels en "
        "toleranties kunnen via validation_options worden aangepast. Per meting "
        "heeft afgekeurd voorrang op onbeslist, en onbeslist op goedgekeurd; "
        "niet-numerieke metingen behouden hun bestaande kwaliteitsstatus. "
        "Bij ten minste 50 metingen wordt de mediaan van positieve meetintervallen "
        "gebruikt, begrensd op een dag en vermenigvuldigd met 24; bij minder "
        "metingen is de cutoff een dag. Bepaalde peilklokjes worden niet gesplitst."
    ),
    request=GLDRegistrationSerializer,
)
class GLDRegistrationView(BaseGLDCorrectionView):
    """Validate and split a complete GLD addition before creating UploadTasks."""

    serializer_class = GLDRegistrationSerializer

    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        organisation = self._get_organisation(request)

        options = data.get("validation_options", {})
        rules = tuple(options.get("rules", DEFAULT_RULES))
        settings = ValidationSettings(
            rules=rules,
            flatline_sigma_multiplier=options.get(
                "flatline_sigma_multiplier",
                DEFAULT_FLATLINE_SIGMA_MULTIPLIER,
            ),
            spike_sigma_multiplier=options.get(
                "spike_sigma_multiplier",
                DEFAULT_SPIKE_SIGMA_MULTIPLIER,
            ),
            tube_top_tolerance=options.get(
                "tube_top_tolerance", DEFAULT_PHYSICAL_TOLERANCE
            ),
            tube_bottom_tolerance=options.get(
                "tube_bottom_tolerance", DEFAULT_PHYSICAL_TOLERANCE
            ),
            sensor_height_tolerance=options.get(
                "sensor_height_tolerance", DEFAULT_PHYSICAL_TOLERANCE
            ),
            sensor_height=options.get("sensor_height"),
        )

        addition = serializer.addition_model
        segments = split_measurements(addition)
        tube_top = tube_bottom = None
        if {"below_tube_top", "above_tube_bottom"}.intersection(rules):
            bro_id = serializer.metadata_model.bro_id
            if not bro_id:
                raise CorrectionValidationError(
                    "metadata.broId is required to validate tube geometry."
                )
            tube_top, tube_bottom = fetch_tube_geometry(bro_id)

        task_payloads: list[
            tuple[UploadTaskMetadata, dict[str, Any], tuple[str, str, str]]
        ] = []
        for index, segment in enumerate(segments, start=1):
            validate_measurements(
                segment,
                settings,
                tube_top=tube_top,
                tube_bottom=tube_bottom,
            )
            segmented_addition = build_segment_addition(addition, segment)
            metadata = serializer.metadata_model.model_copy(deep=True)
            if len(segments) > 1:
                metadata.request_reference = (
                    f"{metadata.request_reference}_{index}_{uuid.uuid4().hex[:8]}"
                )
            task_payloads.append(
                (
                    metadata,
                    segmented_addition.model_dump(
                        mode="json", by_alias=True, exclude_unset=True
                    ),
                    (
                        segmented_addition.begin_position,
                        segmented_addition.end_position,
                        segmented_addition.result_time or "",
                    ),
                )
            )

        upload_tasks = [
            api_models.UploadTask(
                data_owner=organisation,
                bro_domain="GLD",
                project_number=data["project_number"],
                registration_type="GLD_Addition",
                request_type="registration",
                metadata=metadata.model_dump(by_alias=True, exclude_unset=True),
                sourcedocument_data=sourcedocument_data,
            )
            for metadata, sourcedocument_data, _ in task_payloads
        ]
        with transaction.atomic():
            created_tasks = api_models.UploadTask.objects.bulk_create(upload_tasks)

            def start_created_tasks() -> None:
                for task in created_tasks:
                    task.save()

            transaction.on_commit(start_created_tasks)

        return Response(
            {
                "upload_tasks": [
                    {
                        "uuid": str(task.uuid),
                        "begin_position": period[0],
                        "end_position": period[1],
                        "result_time": period[2],
                    }
                    for task, (_, _, period) in zip(created_tasks, task_payloads)
                ]
            },
            status=status.HTTP_201_CREATED,
        )
