from api.bro_import.bro_xml_reader import GMNXML
from api.bro_upload.upload_datamodels import (
    GMNClosure,
    GMNMeasuringPoint,
    GMNMeasuringPointEndDate,
    GMNStartregistration,
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
    start_event = start_registration_event(gmn, measuring_points, events)
    if gmn.end_monitoring_date:
        # The BRO stores a closure as endDateMonitoring, not as an intermediateEvent
        events.append(
            {
                "name": "registratieBeeindigen",
                "date": gmn.end_monitoring_date,
                "measuring_point_code": None,
            }
        )
    for event in events:
        registration_type = GMN_EVENT_MAPPING.get(event["name"])
        if registration_type in SOURCEDOCUMENT_FORMATTER:
            event["registration_type"] = registration_type
            event["tube"] = find_tube(measuring_points, event)
            event["sourcedocument"] = SOURCEDOCUMENT_FORMATTER[registration_type](event)
            event["metadata"] = meta_data_formatter(gmn, event)

    # The registration always starts with a GMN_StartRegistration
    events.insert(0, start_event)

    return {
        "bro_id": bro_id,
        "number_of_events": len(events),
        "events": events,
        "quality_regime": gmn.quality_regime,
    }


def start_registration_event(
    gmn: GMNXML, measuring_points: list[dict], events: list[dict]
) -> dict:
    """
    Build the GMN_StartRegistration. Measuring points that were added later through
    a meetpuntToevoegen event are not part of it.
    """
    added_later = {
        e["measuring_point_code"] for e in events if e["name"] == "meetpuntToevoegen"
    }
    start_date = gmn.start_monitoring_date
    initial_points = []
    for measuring_point in measuring_points:
        code = measuring_point["measuring_point_code"]
        tubes = measuring_point["monitoring_tubes"]
        if code in added_later or not tubes:
            continue
        tube = next(
            (t for t in tubes if t["start_date"] == measuring_point["start_date"]),
            tubes[0],
        )
        initial_points.append(
            {
                "measuring_point_code": code,
                "bro_id": tube["bro_id"],
                "tube_number": tube["tube_nr"],
            }
        )

    event = {
        "name": "startRegistratie",
        "registration_type": "GMN_StartRegistration",
        "date": start_date,
        "measuring_point_code": None,
    }
    # The public BRO does not expose the accountable party's object id
    event["sourcedocument"] = GMNStartregistration(
        object_id_accountable_party=gmn.bro_id,
        name=gmn.name,
        delivery_context=gmn.delivery_context,
        monitoring_purpose=gmn.monitoring_purpose,
        groundwater_aspect=gmn.groundwater_aspect,
        start_date_monitoring=start_date,
        measuring_points=initial_points,
    ).model_dump(by_alias=True)
    event["metadata"] = meta_data_formatter(gmn, event)
    return event


GMN_EVENT_MAPPING = {
    "startRegistratie": "GMN_StartRegistration",
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
