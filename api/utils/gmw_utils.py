import logging

from gmw.models import GMW, Event, MonitoringTube

from .helpers import transformer

logger = logging.getLogger(__name__)


def create_gmw(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    delivered_location = sourcedocument_data.get("deliveredLocation", "0 0").split(" ")
    if delivered_location == "" or len(delivered_location) != 2:
        logger.info(
            f"Invalid deliveredLocation format for bro_id={bro_id}, owner={data_owner}. Expected 'x y', got: {sourcedocument_data.get('deliveredLocation')}"
        )
        rd_x, rd_y = 0.0, 0.0
    else:
        rd_x, rd_y = map(float, delivered_location)

    lon, lat = transformer.transform(rd_x, rd_y)
    standardized_location = f"{lat} {lon}"
    gmw = GMW.objects.update_or_create(
        bro_id=bro_id,
        data_owner=data_owner,
        defaults={
            "internal_id": sourcedocument_data.get("objectIdAccountableParty"),
            "delivery_accountable_party": metadata.get("deliveryAccountableParty"),
            "quality_regime": metadata.get("qualityRegime"),
            "well_construction_date": sourcedocument_data.get("wellConstructionDate"),
            "delivery_context": sourcedocument_data.get("deliveryContext"),
            "construction_standard": sourcedocument_data.get("constructionStandard"),
            "initial_function": sourcedocument_data.get("initialFunction"),
            "ground_level_stable": sourcedocument_data.get("groundLevelStable"),
            "well_stability": sourcedocument_data.get("wellStability"),
            "nitg_code": sourcedocument_data.get("nitgCode"),
            "well_code": sourcedocument_data.get("wellCode"),
            "owner": sourcedocument_data.get("owner"),
            "well_head_protector": sourcedocument_data.get("wellHeadProtector"),
            "delivered_location": sourcedocument_data.get("deliveredLocation"),
            "horizontal_positioning_method": sourcedocument_data.get(
                "horizontalPositioningMethod"
            ),
            "local_vertical_reference_point": sourcedocument_data.get(
                "localVerticalReferencePoint"
            ),
            "offset": sourcedocument_data.get("offset"),
            "vertical_datum": sourcedocument_data.get("verticalDatum"),
            "ground_level_position": sourcedocument_data.get("groundLevelPosition"),
            "ground_level_positioning_method": sourcedocument_data.get(
                "groundLevelPositioningMethod"
            ),
            "standardized_location": standardized_location,
            "registration_status": "geregistreerd",
            "removed": "nee",
        },
    )[0]
    for tube in sourcedocument_data.get("monitoringTubes", []):
        position_tube_top = tube.get("tubeTopPosition")
        plain_tube_length = tube.get("plainTubePartLength")
        screen_top_position = (
            float(position_tube_top) - float(plain_tube_length)
            if (plain_tube_length is not None and position_tube_top is not None)
            else None
        )
        screen_bottom_position = (
            float(screen_top_position) - float(tube.get("screenLength"))
            if (
                screen_top_position is not None and tube.get("screenLength") is not None
            )
            else None
        )
        geo_ohm_cables = tube.get("geoOhmCables", [])
        MonitoringTube.objects.update_or_create(
            gmw=gmw,
            tube_number=tube.get("tubeNumber"),
            data_owner=gmw.data_owner,
            defaults={
                "tube_type": tube.get("tubeType"),
                "artesian_well_cap_present": tube.get("artesianWellCapPresent"),
                "sediment_sump_present": tube.get("sedimentSumpPresent"),
                "sediment_sump_length": tube.get("sedimentSumpLength"),
                "number_of_geo_ohm_cables": tube.get("numberOfGeoOhmCables", 0),
                "geo_ohm_cables": geo_ohm_cables if geo_ohm_cables else [],
                "tube_top_diameter": tube.get("tubeTopDiameter"),
                "variable_diameter": tube.get("variableDiameter"),
                "tube_status": tube.get("tubeStatus"),
                "tube_top_position": position_tube_top,
                "tube_top_positioning_method": tube.get("tubeTopPositioningMethod"),
                "tube_part_inserted": tube.get("tubePartInserted"),
                "tube_in_use": tube.get("tubeInUse"),
                "tube_packing_material": tube.get("tubePackingMaterial"),
                "tube_material": tube.get("tubeMaterial"),
                "glue": tube.get("glue"),
                "screen_length": tube.get("screenLength"),
                "screen_protection": tube.get("screenProtection"),
                "sock_material": tube.get("sockMaterial"),
                "screen_top_position": screen_top_position,
                "screen_bottom_position": screen_bottom_position,
                "plain_tube_part_length": plain_tube_length,
            },
        )

    logger.info(f"Sucessfully created {gmw} with {gmw.tubes.count()} monitoring tubes.")
    return


def create_gmw_event(
    *,
    bro_id: str,
    event_type: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    """Generic factory for creating GMW events."""
    try:
        gmw = GMW.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GMW.DoesNotExist:
        logger.info(f"GMW not found for bro_id={bro_id}, owner={data_owner}")
        return
    except GMW.MultipleObjectsReturned:
        gmw = (
            GMW.objects.filter(bro_id=bro_id, data_owner=data_owner)
            .order_by("created_at")
            .first()
        )

    Event.objects.update_or_create(
        gmw=gmw,
        event_name=event_type,
        event_date=sourcedocument_data.get("eventDate"),
        data_owner=data_owner,
        defaults={
            "metadata": metadata,
            "sourcedocument_data": sourcedocument_data,
        },
    )


def create_gmw_removal(
    bro_id: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    """Generic factory for creating GMW events."""
    try:
        gmw = GMW.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GMW.DoesNotExist:
        logger.info(f"GMW not found for bro_id={bro_id}, owner={data_owner}")
        return
    except GMW.MultipleObjectsReturned:
        gmw = (
            GMW.objects.filter(bro_id=bro_id, data_owner=data_owner)
            .order_by("created_at")
            .first()
        )

    Event.objects.update_or_create(
        gmw=gmw,
        event_name="GMW_Removal",
        data_owner=data_owner,
        defaults={
            "event_date": sourcedocument_data.get("eventDate"),
            "metadata": metadata,
            "sourcedocument_data": sourcedocument_data,
        },
    )

    gmw.removed = "ja"
    gmw.save(update_fields=["removed"])


# ── Update functions ──────────────────────────────────────────────────────────


def update_gmw(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    try:
        gmw = GMW.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GMW.DoesNotExist:
        logger.info(f"GMW not found for bro_id={bro_id}, owner={data_owner}")
        return
    except GMW.MultipleObjectsReturned:
        gmw = (
            GMW.objects.filter(bro_id=bro_id, data_owner=data_owner)
            .order_by("created_at")
            .first()
        )

    source_field_map = {
        "internal_id": "objectIdAccountableParty",
        "well_construction_date": "wellConstructionDate",
        "delivery_context": "deliveryContext",
        "construction_standard": "constructionStandard",
        "initial_function": "initialFunction",
        "ground_level_stable": "groundLevelStable",
        "well_stability": "wellStability",
        "nitg_code": "nitgCode",
        "well_code": "wellCode",
        "owner": "owner",
        "well_head_protector": "wellHeadProtector",
        "delivered_location": "deliveredLocation",
        "horizontal_positioning_method": "horizontalPositioningMethod",
        "local_vertical_reference_point": "localVerticalReferencePoint",
        "offset": "offset",
        "vertical_datum": "verticalDatum",
        "ground_level_position": "groundLevelPosition",
        "ground_level_positioning_method": "groundLevelPositioningMethod",
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
    if "deliveredLocation" in sourcedocument_data:
        delivered_location = sourcedocument_data.get("deliveredLocation", "0 0").split(
            " "
        )
        if len(delivered_location) == 2:
            rd_x, rd_y = map(float, delivered_location)
            lon, lat = transformer.transform(rd_x, rd_y)
            updates["standardized_location"] = f"{lat} {lon}"

    for field, value in updates.items():
        setattr(gmw, field, value)
    if updates:
        gmw.save(update_fields=list(updates.keys()))
    logger.info(f"Successfully updated {gmw}.")

    monitoring_tubes_data = sourcedocument_data.get("monitoringTubes", [])
    for tube in monitoring_tubes_data:
        tube_number = tube.get("tubeNumber", 1)

        MonitoringTube.objects.update_or_create(
            gmw=gmw,
            tube_number=tube_number,
            data_owner=data_owner,
            defaults={
                "tube_type": tube.get("tubeType"),
                "artesian_well_cap_present": tube.get("artesianWellCapPresent"),
                "sediment_sump_present": tube.get("sedimentSumpPresent"),
                "sediment_sump_length": tube.get("sedimentSumpLength"),
                "number_of_geo_ohm_cables": tube.get("numberOfGeoOhmCables", 0),
                "geo_ohm_cables": tube.get("geoOhmCables", []),
                "tube_top_diameter": tube.get("tubeTopDiameter"),
                "variable_diameter": tube.get("variableDiameter"),
                "tube_status": tube.get("tubeStatus"),
                "tube_top_position": tube.get("tubeTopPosition"),
                "tube_top_positioning_method": tube.get("tubeTopPositioningMethod"),
                "tube_part_inserted": tube.get("tubePartInserted"),
                "tube_in_use": tube.get("tubeInUse"),
                "tube_packing_material": tube.get("tubePackingMaterial"),
                "tube_material": tube.get("tubeMaterial"),
                "glue": tube.get("glue"),
                "screen_length": tube.get("screenLength"),
                "screen_protection": tube.get("screenProtection"),
                "sock_material": tube.get("sockMaterial"),
                "plain_tube_part_length": tube.get("plainTubePartLength"),
            },
        )


def update_gmw_event(
    *,
    bro_id: str,
    event_type: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    try:
        gmw = GMW.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GMW.DoesNotExist:
        logger.info(f"GMW not found for bro_id={bro_id}, owner={data_owner}")
        return
    except GMW.MultipleObjectsReturned:
        gmw = (
            GMW.objects.filter(bro_id=bro_id, data_owner=data_owner)
            .order_by("created_at")
            .first()
        )

    date_to_correct = sourcedocument_data.get("dateToBeCorrected")
    request_type = "move" if date_to_correct else "replace"

    event_qs = Event.objects.filter(
        gmw=gmw, event_name=event_type, data_owner=data_owner
    )
    if request_type == "move":
        event_qs = event_qs.filter(event_date=date_to_correct)
    else:
        event_qs = event_qs.filter(event_date=sourcedocument_data.get("eventDate"))

    if event_qs.count() != 1:
        logger.warning(
            f"Expected to find exactly 1 event for bro_id={bro_id}, event_type={event_type}, date={date_to_correct}, but found {event_qs.count()}. Skipping update."
        )
        return

    event = event_qs.first()
    if not event:
        logger.info(
            f"Event {event_type} not found for bro_id={bro_id}, date={date_to_correct}. Creating new event."
        )

        ## FUTURE: Make sure that the sourcedocument and metadata are formatted correctly
        # Currently this creates, not updates the right event.
        Event.objects.update(
            gmw=gmw,
            event_name=event_type,
            event_date=sourcedocument_data.get("eventDate"),
            metadata=metadata,
            sourcedocument_data=sourcedocument_data,
            data_owner=data_owner,
        )
        return

    update_fields = ["metadata", "sourcedocument_data"]
    event.metadata = metadata
    event.sourcedocument_data = sourcedocument_data
    new_event_date = sourcedocument_data.get("eventDate")
    if new_event_date:
        event.event_date = new_event_date
        update_fields.append("event_date")
    event.save(update_fields=update_fields)


def update_gmw_removal(
    bro_id: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    try:
        gmw = GMW.objects.get(bro_id=bro_id, data_owner=data_owner)
    except GMW.DoesNotExist:
        logger.info(f"GMW not found for bro_id={bro_id}, owner={data_owner}")
        return
    except GMW.MultipleObjectsReturned:
        gmw = (
            GMW.objects.filter(bro_id=bro_id, data_owner=data_owner)
            .order_by("created_at")
            .first()
        )

    date_to_correct = sourcedocument_data.get("dateToBeCorrected")
    event_qs = Event.objects.filter(
        gmw=gmw, event_name="GMW_Removal", data_owner=data_owner
    )
    if date_to_correct:
        event_qs = event_qs.filter(event_date=date_to_correct)

    event = event_qs.order_by("-event_date").first()
    if not event:
        logger.info(
            f"GMW_Removal event not found for bro_id={bro_id}, date={date_to_correct}."
        )
        return

    update_fields = ["metadata", "sourcedocument_data"]
    event.metadata = metadata
    event.sourcedocument_data = sourcedocument_data
    new_event_date = sourcedocument_data.get("eventDate")
    if new_event_date:
        event.event_date = new_event_date
        update_fields.append("event_date")
    event.save(update_fields=update_fields)
