import datetime
import logging

from gmn.models import GMN, IntermediateEvent, Measuringpoint

logger = logging.getLogger(__name__)


def find_linked_gmns(gmn_bro_ids: list[str] | str) -> list[GMN]:
    if isinstance(gmn_bro_ids, str):
        gmn_bro_ids = [gmn_bro_ids]
    gmns = GMN.objects.filter(bro_id__in=gmn_bro_ids)
    if len(gmns) != len(gmn_bro_ids):
        found_bro_ids = {gmn.bro_id for gmn in gmns}
        missing = set(gmn_bro_ids) - found_bro_ids
        logger.info(f"Could not find GMNs with bro_id(s): {', '.join(missing)}")
    return list(gmns)


def create_gmn(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    GMN.objects.update_or_create(
        bro_id=bro_id,
        data_owner=data_owner,
        defaults={
            "internal_id": sourcedocument_data.get("objectIdAccountableParty"),
            "quality_regime": metadata.get("qualityRegime"),
            "name": sourcedocument_data.get("name"),
            "delivery_context": sourcedocument_data.get("deliveryContext"),
            "monitoring_purpose": sourcedocument_data.get("monitoringPurpose"),
            "groundwater_aspect": sourcedocument_data.get("groundwaterAspect"),
            "start_date_monitoring": sourcedocument_data.get("startDateMonitoring"),
        },
    )
    return


def create_gmn_measuringpoint(
    *,
    bro_id: str,
    event_type: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    """Generic factory for creating GMN Measuring Points."""
    try:
        gmn = GMN.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GMN.DoesNotExist:
        logger.info(f"GMN not found for bro_id={bro_id}, owner={data_owner}")
        return

    last_measuring_point = (
        Measuringpoint.objects.filter(
            gmn=gmn,
            measuringpoint_code=sourcedocument_data.get("measuringPointCode"),
            data_owner=data_owner,
            tube_start_date__lt=sourcedocument_data.get("eventDate"),
        )
        .order_by("-tube_start_date")
        .first()
    )

    Measuringpoint.objects.update_or_create(
        gmn=gmn,
        data_owner=data_owner,
        measuringpoint_code=sourcedocument_data.get("measuringPointCode"),
        gmw_bro_id=sourcedocument_data.get(
            "broId"
        ),  # In GMN MeasuringPoint model, broId instead of gmwBroId is used.
        tube_number=sourcedocument_data.get("tubeNumber"),
        event_type=event_type,
        defaults={
            "tube_start_date": sourcedocument_data.get("eventDate"),
            "measuringpoint_start_date": last_measuring_point.measuringpoint_start_date
            if last_measuring_point
            else sourcedocument_data.get("eventDate"),
        },
    )

    if last_measuring_point and event_type == "GMN_MeasuringPointEndDate":
        # Set all measuring points that started before this end date to have this end date
        Measuringpoint.objects.filter(
            gmn=gmn,
            measuringpoint_code=sourcedocument_data.get("measuringPointCode"),
            data_owner=data_owner,
            tube_start_date__lt=datetime.datetime.strptime(
                sourcedocument_data.get("eventDate", "1900-01-01"), "%Y-%m-%d"
            ),
        ).update(
            measuringpoint_end_date=sourcedocument_data.get("eventDate"),
        )

        last_measuring_point.refresh_from_db()
        # Update the last tube to have the tube_end_date as well
        last_measuring_point.tube_end_date = sourcedocument_data.get("eventDate")
        last_measuring_point.save(update_fields=["tube_end_date"])

    elif last_measuring_point and event_type == "GMN_TubeReference":
        last_measuring_point.tube_end_date = sourcedocument_data.get("eventDate")
        last_measuring_point.save(update_fields=["tube_end_date"])


# ── Update functions ──────────────────────────────────────────────────────────


def update_gmn(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    try:
        gmn = GMN.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GMN.DoesNotExist:
        logger.info(f"GMN not found for bro_id={bro_id}, owner={data_owner}")
        return

    source_field_map = {
        "internal_id": "objectIdAccountableParty",
        "name": "name",
        "delivery_context": "deliveryContext",
        "monitoring_purpose": "monitoringPurpose",
        "groundwater_aspect": "groundwaterAspect",
        "start_date_monitoring": "startDateMonitoring",
    }
    meta_field_map = {
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
        setattr(gmn, field, value)
    if updates:
        gmn.save(update_fields=list(updates.keys()))


def update_enddate_gmn(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    try:
        gmn = GMN.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GMN.DoesNotExist:
        logger.info(f"GMN not found for bro_id={bro_id}, owner={data_owner}")
        return

    end_date_monitoring = sourcedocument_data.get("endDateMonitoring")
    gmn.end_date_monitoring = end_date_monitoring
    gmn.save(update_fields=["end_date_monitoring"])


def remove_enddate_gmn(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    try:
        gmn = GMN.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GMN.DoesNotExist:
        logger.info(f"GMN not found for bro_id={bro_id}, owner={data_owner}")
        return

    gmn.end_date_monitoring = None
    gmn.save(update_fields=["end_date_monitoring"])


def update_gmn_measuringpoint(
    *,
    bro_id: str,
    event_type: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    try:
        gmn = GMN.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GMN.DoesNotExist:
        logger.info(f"GMN not found for bro_id={bro_id}, owner={data_owner}")
        return

    date_to_correct = sourcedocument_data.get("dateToBeCorrected")
    mp_qs = Measuringpoint.objects.filter(
        gmn=gmn,
        measuringpoint_code=sourcedocument_data.get("measuringPointCode"),
        data_owner=data_owner,
        event_type=event_type,
    )
    if date_to_correct:
        mp_qs = mp_qs.filter(tube_start_date=date_to_correct)

    measuringpoint = mp_qs.order_by("-tube_start_date").first()
    if not measuringpoint:
        logger.info(
            f"Measuringpoint not found for bro_id={bro_id}, "
            f"code={sourcedocument_data.get('measuringPointCode')}, date={date_to_correct}."
        )
        return

    source_field_map = {
        "gmw_bro_id": "broId",
        "tube_number": "tubeNumber",
        "tube_start_date": "eventDate",
    }
    updates = {
        field: sourcedocument_data[key]
        for field, key in source_field_map.items()
        if key in sourcedocument_data
    }
    for field, value in updates.items():
        setattr(measuringpoint, field, value)
    if updates:
        measuringpoint.save(update_fields=list(updates.keys()))


# ── Delete functions ──────────────────────────────────────────────────────────


def delete_gmn_intermediate_event(
    bro_id: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    try:
        gmn = GMN.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GMN.DoesNotExist:
        logger.info(f"GMN not found for bro_id={bro_id}, owner={data_owner}")
        return

    date_to_correct = sourcedocument_data.get("dateToBeCorrected")
    event_qs = IntermediateEvent.objects.filter(gmn=gmn, data_owner=data_owner)
    if date_to_correct:
        event_qs = event_qs.filter(event_date=date_to_correct)

    deleted_count, _ = event_qs.delete()
    logger.info(
        f"Deleted {deleted_count} intermediate event(s) for bro_id={bro_id}, date={date_to_correct}."
    )
