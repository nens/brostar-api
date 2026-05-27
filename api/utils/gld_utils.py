import logging

from gld.models import GLD, Observation

logger = logging.getLogger(__name__)


def create_gld(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    GLD.objects.update_or_create(
        bro_id=bro_id,
        data_owner=data_owner,
        defaults={
            "internal_id": sourcedocument_data.get("objectIdAccountableParty"),
            "delivery_accountable_party": metadata.get("deliveryAccountableParty"),
            "linked_gmns": sourcedocument_data.get("linkedGmns", []),
            "quality_regime": metadata.get("qualityRegime"),
            "gmw_bro_id": sourcedocument_data.get("gmwBroId"),
            "tube_number": sourcedocument_data.get("tubeNumber"),
        },
    )
    return


def create_gld_addition(
    bro_id: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    """Generic factory for creating GLD Observations."""
    try:
        gld = GLD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GLD.DoesNotExist:
        logger.info(f"GLD not found for bro_id={bro_id}, owner={data_owner}")
        return

    Observation.objects.update_or_create(
        gld=gld,
        observation_id=sourcedocument_data.get("observationId"),
        data_owner=data_owner,
        defaults={
            "begin_position": sourcedocument_data.get("beginPosition"),
            "end_position": sourcedocument_data.get("endPosition"),
            "result_time": sourcedocument_data.get("resultTime"),
            "validation_status": sourcedocument_data.get("validationStatus"),
            "investigator_kvk": sourcedocument_data.get("investigatorKvk"),
            "observation_type": sourcedocument_data.get("observationType"),
            "process_reference": sourcedocument_data.get("processReference"),
            "air_pressure_compensation_type": sourcedocument_data.get(
                "airPressureCompensationType"
            ),
            "evaluation_procedure": sourcedocument_data.get("evaluationProcedure"),
            "measurement_instrument_type": sourcedocument_data.get(
                "measurementInstrumentType"
            ),
        },
    )


# ── Update functions ──────────────────────────────────────────────────────────


def update_gld(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    try:
        gld = GLD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GLD.DoesNotExist:
        logger.info(f"GLD not found for bro_id={bro_id}, owner={data_owner}")
        return

    source_field_map = {
        "internal_id": "objectIdAccountableParty",
        "linked_gmns": "linkedGmns",
        "gmw_bro_id": "gmwBroId",
        "tube_number": "tubeNumber",
    }
    meta_field_map = {
        "delivery_accountable_party": "deliveryAccountableParty",
        "quality_regime": "qualityRegime",
    }
    updates = {
        field: sourcedocument_data[key]
        for field, key in source_field_map.items()
        if key in sourcedocument_data
    }
    updates.update(
        {
            field: metadata[key]
            for field, key in meta_field_map.items()
            if key in metadata
        }
    )
    for field, value in updates.items():
        setattr(gld, field, value)
    if updates:
        gld.save(update_fields=list(updates.keys()))


def update_gld_observation(
    bro_id: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    try:
        gld = GLD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GLD.DoesNotExist:
        logger.info(f"GLD not found for bro_id={bro_id}, owner={data_owner}")
        return

    date_to_correct = sourcedocument_data.get("dateToBeCorrected")
    obs_qs = Observation.objects.filter(gld=gld, data_owner=data_owner)
    if date_to_correct:
        obs_qs = obs_qs.filter(begin_position=date_to_correct)

    observation = obs_qs.order_by("-begin_position").first()
    if not observation:
        logger.info(
            f"Observation not found for bro_id={bro_id}, date={date_to_correct}."
        )
        return

    source_field_map = {
        "begin_position": "beginPosition",
        "end_position": "endPosition",
        "result_time": "resultTime",
        "validation_status": "validationStatus",
        "investigator_kvk": "investigatorKvk",
        "observation_type": "observationType",
        "process_reference": "processReference",
        "air_pressure_compensation_type": "airPressureCompensationType",
        "evaluation_procedure": "evaluationProcedure",
        "measurement_instrument_type": "measurementInstrumentType",
    }
    updates = {
        field: sourcedocument_data[key]
        for field, key in source_field_map.items()
        if key in sourcedocument_data
    }
    for field, value in updates.items():
        setattr(observation, field, value)
    if updates:
        observation.save(update_fields=list(updates.keys()))


# ── Delete functions ──────────────────────────────────────────────────────────


def delete_gld_observation(
    bro_id: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    try:
        gld = GLD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GLD.DoesNotExist:
        logger.info(f"GLD not found for bro_id={bro_id}, owner={data_owner}")
        return

    date_to_correct = sourcedocument_data.get("dateToBeCorrected")
    obs_qs = Observation.objects.filter(gld=gld, data_owner=data_owner)
    if date_to_correct:
        obs_qs = obs_qs.filter(begin_position=date_to_correct)

    deleted_count, _ = obs_qs.delete()
    logger.info(
        f"Deleted {deleted_count} observation(s) for bro_id={bro_id}, date={date_to_correct}."
    )
