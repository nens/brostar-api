from api.bro_import.bro_xml_reader import GMWXML
from api.bro_upload.upload_datamodels import (
    GMWElectrodeStatus,
    GMWGroundLevel,
    GMWGroundLevelMeasuring,
    GMWInsertion,
    GMWLengthening,
    GMWPositions,
    GMWPositionsMeasuring,
    GMWShift,
    GMWShortening,
    GMWTubeStatus,
    GMWWellHeadProtector,
    UploadTaskMetadata,
)


def history_importer(bro_id: str) -> dict:
    gmw = GMWXML(bro_id)
    events = gmw.intermediate_events
    for event in events:
        registration_type = registration_type_finder(event.get("eventName"))
        if registration_type and registration_type in SOURCEDOCUMENT_FORMATTER:
            event["sourcedocument"] = SOURCEDOCUMENT_FORMATTER[registration_type](event)
            event["metadata"] = meta_data_formatter(gmw, event)

    return {
        "bro_id": bro_id,
        "number_of_events": len(events),
        "events": events,
        "quality_regime": gmw.quality_regime,
    }


GMW_EVENT_MAPPING = {
    "beschermconstructieVeranderd": "GMW_WellHeadProtector",
    "buisdeelIngeplaatst": "GMW_Insertion",
    "buisIngekort": "GMW_Shortening",
    "buisOpgelengd": "GMW_Lengthening",
    "buisstatusVeranderd": "GMW_TubeStatus",
    "eigenaarVeranderd": "GMW_Owner",
    "elektrodestatusVeranderd": "GMW_ElectrodeStatus",
    "maaiveldVerlegd": "GMW_Shift",
    "nieuweBepalingMaaiveld": "GMW_GroundLevel",
    "nieuweBepalingPosities": "GMW_Positions",
    "nieuweInmetingMaaiveld": "GMW_GroundLevelMeasuring",
    "nieuweInmetingPosities": "GMW_PositionsMeasuring",
    "onderhouderVeranderd": "GMW_Maintainer",
}


def well_head_extractor(event: dict) -> dict:
    well_data = event.get("wellData", {})
    well_head_data = GMWWellHeadProtector(
        event_date=event.get("eventDate"),
        well_head_protector=well_data.get("wellHeadProtector"),
    )
    return well_head_data.model_dump(by_alias=True)


def lengthening_extractor(event: dict) -> dict:
    well_data = event.get("wellData", {})
    lengthening_data = GMWLengthening(
        event_date=event.get("eventDate"),
        well_head_protector=well_data.get("wellHeadProtector"),
        monitoring_tubes=event.get("tubeData", []),
    )
    return lengthening_data.model_dump(by_alias=True)


def shortening_extractor(event: dict) -> dict:
    well_data = event.get("wellData", {})
    shortening_data = GMWShortening(
        event_date=event.get("eventDate"),
        well_head_protector=well_data.get("wellHeadProtector"),
        monitoring_tubes=event.get("tubeData", []),
    )
    return shortening_data.model_dump(by_alias=True)


def tube_status_extractor(event: dict) -> dict:
    tube_status_data = GMWTubeStatus(
        event_date=event.get("eventDate"),
        monitoring_tubes=event.get("tubeData", []),
    )
    return tube_status_data.model_dump(by_alias=True)


def insertion_extractor(event: dict) -> dict:
    insertion_data = GMWInsertion(
        event_date=event.get("eventDate"),
        monitoring_tubes=event.get("tubeData", []),
    )
    return insertion_data.model_dump(by_alias=True)


def electrode_status_extractor(event: dict) -> dict:
    electrode_status_data = GMWElectrodeStatus(
        event_date=event.get("eventDate"),
        electrodes=event.get("electrodeData", []),
    )
    return electrode_status_data.model_dump(by_alias=True)


def ground_level_extractor(event: dict) -> dict:
    well_data = event.get("wellData", {})
    ground_level_data = GMWGroundLevel(
        event_date=event.get("eventDate"),
        ground_level_position=well_data.get("groundLevelPosition"),
        ground_level_positioning_method=well_data.get("groundLevelPositioningMethod"),
    )
    return ground_level_data.model_dump(by_alias=True)


def ground_level_measuring_extractor(event: dict) -> dict:
    well_data = event.get("wellData", {})
    ground_level_measuring_data = GMWGroundLevelMeasuring(
        event_date=event.get("eventDate"),
        ground_level_position=well_data.get("groundLevelPosition"),
        ground_level_positioning_method=well_data.get("groundLevelPositioningMethod"),
    )
    return ground_level_measuring_data.model_dump(by_alias=True)


def positions_extractor(event: dict) -> dict:
    well_data = event.get("wellData", {})
    positions_data = GMWPositions(
        event_date=event.get("eventDate"),
        ground_level_position=well_data.get("groundLevelPosition"),
        ground_level_positioning_method=well_data.get("groundLevelPositioningMethod"),
        monitoring_tubes=event.get("tubeData", []),
    )
    return positions_data.model_dump(by_alias=True)


def positions_measuring_extractor(event: dict) -> dict:
    well_data = event.get("wellData", {})
    positions_measuring_data = GMWPositionsMeasuring(
        event_date=event.get("eventDate"),
        ground_level_position=well_data.get("groundLevelPosition"),
        ground_level_positioning_method=well_data.get("groundLevelPositioningMethod"),
        monitoring_tubes=event.get("tubeData", []),
    )
    return positions_measuring_data.model_dump(by_alias=True)


def shift_extractor(event: dict) -> dict:
    well_data = event.get("wellData", {})
    shift_data = GMWShift(
        event_date=event.get("eventDate"),
        ground_level_position=well_data.get("groundLevelPosition"),
        ground_level_positioning_method=well_data.get("groundLevelPositioningMethod"),
    )
    return shift_data.model_dump(by_alias=True)


SOURCEDOCUMENT_FORMATTER = {
    "GMW_WellHeadProtector": well_head_extractor,
    "GMW_Lengthening": lengthening_extractor,
    "GMW_Shortening": shortening_extractor,
    "GMW_TubeStatus": tube_status_extractor,
    "GMW_Insertion": insertion_extractor,
    "GMW_ElectrodeStatus": electrode_status_extractor,
    "GMW_GroundLevel": ground_level_extractor,
    "GMW_GroundLevelMeasuring": ground_level_measuring_extractor,
    "GMW_Positions": positions_extractor,
    "GMW_PositionsMeasuring": positions_measuring_extractor,
    "GMW_Shift": shift_extractor,
}


def registration_type_finder(event_name: str) -> str | None:
    return GMW_EVENT_MAPPING.get(event_name)


def meta_data_formatter(gmw: GMWXML, event: dict) -> dict:
    metadata = UploadTaskMetadata(
        request_reference=f"{gmw.bro_id}_{event['eventName']}_{event['eventDate']}",
        delivery_accountable_party=gmw.delivery_accountable_party,
        bro_id=gmw.bro_id,
        quality_regime=gmw.quality_regime,
    )
    return metadata.model_dump(by_alias=True)
