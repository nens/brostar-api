from api.bro_import.bro_xml_reader import GMNXML
from api.bro_upload.upload_datamodels import (
    GMNClosure,
    GMNMeasuringPoint,
    GMNMeasuringPointEndDate,
    GMNTubeReference,
    UploadTaskMetadata,
)


def find_tube(measuring_points: list[dict], event: dict) -> dict | None:
    """Return the tube that was linked to the measuring point on the event date."""
    for measuring_point in measuring_points:
        if measuring_point["measuring_point_code"] != event["measuring_point_code"]:
            continue
        for tube in measuring_point["monitoring_tubes"]:
            if tube["start_date"] == event["date"]:
                return tube
    return None


BRO_URL = "https://publiek.broservices.nl/"


def gmn_history_importer(bro_id: str) -> dict:
    gmn = GMNXML(bro_id, bro_url=BRO_URL)
    measuring_points = gmn.measuring_points
    events = gmn.intermediate_events
    for event in events:
        registration_type = GMN_EVENT_MAPPING.get(event["name"])
        if registration_type in SOURCEDOCUMENT_FORMATTER:
            event["tube"] = find_tube(measuring_points, event)
            event["sourcedocument"] = SOURCEDOCUMENT_FORMATTER[registration_type](event)
            event["metadata"] = meta_data_formatter(gmn, event)

    return {
        "bro_id": bro_id,
        "number_of_events": len(events),
        "events": events,
        "quality_regime": gmn.quality_regime,
    }


GMN_EVENT_MAPPING = {
    "meetpuntToevoegen": "GMN_MeasuringPoint",
    "meetpuntBeeindigen": "GMN_MeasuringPointEndDate",
    "monitoringbuisVervangen": "GMN_TubeReference",
    "registratieBeeindigen": "GMN_Closure",
}


def measuring_point_extractor(event: dict) -> dict:
    measuring_point_data = GMNMeasuringPoint(
        event_date=event["date"],
        measuring_point_code=event["measuring_point_code"],
        bro_id=event["tube"]["bro_id"],
        tube_number=event["tube"]["tube_nr"],
    )
    return measuring_point_data.model_dump(by_alias=True)


def tube_reference_extractor(event: dict) -> dict:
    tube_reference_data = GMNTubeReference(
        event_date=event["date"],
        measuring_point_code=event["measuring_point_code"],
        bro_id=event["tube"]["bro_id"],
        tube_number=event["tube"]["tube_nr"],
    )
    return tube_reference_data.model_dump(by_alias=True)


def measuring_point_end_date_extractor(event: dict) -> dict:
    end_date_data = GMNMeasuringPointEndDate(
        event_date=event["date"],
        measuring_point_code=event["measuring_point_code"],
    )
    return end_date_data.model_dump(by_alias=True)


def closure_extractor(event: dict) -> dict:
    closure_data = GMNClosure(end_date_monitoring=event["date"])
    return closure_data.model_dump(by_alias=True)


SOURCEDOCUMENT_FORMATTER = {
    "GMN_MeasuringPoint": measuring_point_extractor,
    "GMN_TubeReference": tube_reference_extractor,
    "GMN_MeasuringPointEndDate": measuring_point_end_date_extractor,
    "GMN_Closure": closure_extractor,
}


def meta_data_formatter(gmn: GMNXML, event: dict) -> dict:
    request_reference = f"{gmn.bro_id}_{event['name']}_{event['date']}"
    if event["measuring_point_code"]:
        request_reference += f"_{event['measuring_point_code']}"

    metadata = UploadTaskMetadata(
        request_reference=request_reference,
        delivery_accountable_party=gmn.delivery_accountable_party,
        bro_id=gmn.bro_id,
        quality_regime=gmn.quality_regime,
    )
    return metadata.model_dump(by_alias=True)
