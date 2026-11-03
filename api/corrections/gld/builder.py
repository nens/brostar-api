"""Build the UploadTask payload for a GLD correction."""

import uuid
from typing import Any

from api.bro_upload.upload_datamodels import (
    GLDAddition,
    TimeValuePair,
    UploadTaskMetadata,
)

from ..exceptions import CorrectionValidationError
from .xml_reader import Measurement, ParsedGLD, ParsedObservation


def build_metadata(parsed: ParsedGLD, correction_reason: str) -> UploadTaskMetadata:
    return UploadTaskMetadata(
        request_reference=f"GLD_Addition_correction_{parsed.bro_id}_{uuid.uuid4().hex[:8]}",
        delivery_accountable_party=parsed.delivery_accountable_party,
        bro_id=parsed.bro_id,
        quality_regime=parsed.quality_regime or "IMBRO",
        correction_reason=correction_reason,
    )


def build_addition(
    observation: ParsedObservation,
    procedure: dict[str, Any],
    measurements: list[Measurement],
    investigator_kvk: str,
    begin_position: str,
    end_position: str,
    result_time: str | None,
) -> GLDAddition:
    """Rebuild the complete GLD_Addition, reusing the existing BRO identifiers."""
    if not observation.measurement_timeseries_id:
        raise CorrectionValidationError(
            f"Observatie {observation.observation_id} bevat geen "
            "MeasurementTimeseries; corrigeren is niet mogelijk."
        )

    return GLDAddition(
        date=observation.date_stamp,
        observation_id=observation.observation_id,
        observation_process_id=observation.observation_process_id,
        measurement_timeseries_id=observation.measurement_timeseries_id,
        validation_status=procedure.get("validation_status"),
        investigator_kvk=investigator_kvk,
        observation_type=procedure.get("observation_type") or "reguliereMeting",
        evaluation_procedure=procedure.get("evaluation_procedure"),
        measurement_instrument_type=procedure.get("measurement_instrument_type"),
        process_reference=procedure.get("process_reference"),
        air_pressure_compensation_type=procedure.get("air_pressure_compensation_type"),
        begin_position=begin_position,
        end_position=end_position,
        result_time=result_time,
        repeat_procedure=observation.repeat_procedure,
        time_value_pairs=[
            TimeValuePair(**measurement.as_payload()) for measurement in measurements
        ],
    )
