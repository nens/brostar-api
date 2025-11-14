import datetime
import logging
from functools import partial

from pyproj import Transformer

from frd.models import FRD
from gld.models import GLD, Observation
from gmn.models import GMN, Measuringpoint
from gmw.models import GMW, Event, MonitoringTube

logger = logging.getLogger(__name__)

# Define transformer from RD New (EPSG:28992) to ETRS89 (EPSG:4258 = lat/lon)
transformer = Transformer.from_crs("EPSG:28992", "EPSG:4258", always_xy=True)


def create_gmw(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    delivered_location = sourcedocument_data.get("deliveredLocation", "0 0").split(" ")
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
        MonitoringTube.objects.update_or_create(
            gmw=gmw,
            data_owner=gmw.data_owner,
            defaults={
                "tube_number": tube.get("tubeNumber"),
                "tube_type": tube.get("tubeType"),
                "artesian_well_cap_present": tube.get("artesianWellCapPresent"),
                "sediment_sump_present": tube.get("sedimentSumpPresent"),
                "sediment_sump_length": tube.get("sedimentSumpLength"),
                "number_of_geo_ohm_cables": tube.get("numberOfGeoOhmCables", 0),
                "geo_ohm_cables": tube.get("geoOhmCables", []),
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

    Event.objects.update_or_create(
        gmw=gmw,
        event_name="GMW_Removal",
        event_date=sourcedocument_data.get("eventDate"),
        data_owner=data_owner,
        defaults={
            "metadata": metadata,
            "sourcedocument_data": sourcedocument_data,
        },
    )

    gmw.removed = "ja"
    gmw.save(update_fields=["removed"])


def find_linked_gmns(gmn_bro_ids: list[str] | str) -> list[GMN]:
    if isinstance(gmn_bro_ids, str):
        gmn_bro_ids = [gmn_bro_ids]
    gmns = GMN.objects.filter(bro_id__in=gmn_bro_ids)
    if len(gmns) != len(gmn_bro_ids):
        found_bro_ids = {gmn.bro_id for gmn in gmns}
        missing = set(gmn_bro_ids) - found_bro_ids
        logger.info(f"Could not find GMNs with bro_id(s): {', '.join(missing)}")
    return list(gmns)


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
            measuringpoint_code=sourcedocument_data.get("measuringpointCode"),
            data_owner=data_owner,
            tube_start_date__lt=sourcedocument_data.get("eventDate"),
        )
        .order_by("-tube_start_date")
        .first()
    )

    Measuringpoint.objects.update_or_create(
        gmn=gmn,
        data_owner=data_owner,
        measuringpoint_code=sourcedocument_data.get("measuringpointCode"),
        gmw_bro_id=sourcedocument_data.get("gmwBroId"),
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
            measuringpoint_code=sourcedocument_data.get("measuringpointCode"),
            data_owner=data_owner,
            tube_start_date__lt=datetime.datetime.strptime(
                sourcedocument_data.get("eventDate"), "%Y-%m-%d"
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


def create_frd(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    FRD.objects.update_or_create(
        bro_id=bro_id,
        data_owner=data_owner,
        defaults={
            "internal_id": sourcedocument_data.get("objectIdAccountableParty"),
            "delivery_accountable_party": sourcedocument_data.get(
                "deliveryAccountableParty"
            ),
            "quality_regime": metadata.get("qualityRegime"),
            "gmw_bro_id": sourcedocument_data.get("gmwBroId"),
            "tube_number": sourcedocument_data.get("tubeNumber"),
        },
    )
    return


# Build mapping with pre-bound event types
CREATE_FUNCTION_MAPPING = {
    "GMW_Construction": create_gmw,
    "GMW_Positions": partial(create_gmw_event, event_type="GMW_Positions"),
    "GMW_PositionsMeasuring": partial(
        create_gmw_event, event_type="GMW_PositionsMeasuring"
    ),
    "GMW_WellHeadProtector": partial(
        create_gmw_event, event_type="GMW_WellHeadProtector"
    ),
    "GMW_Owner": partial(create_gmw_event, event_type="GMW_Owner"),
    "GMW_Shift": partial(create_gmw_event, event_type="GMW_Shift"),
    "GMW_GroundLevel": partial(create_gmw_event, event_type="GMW_GroundLevel"),
    "GMW_GroundLevelMeasuring": partial(
        create_gmw_event, event_type="GMW_GroundLevelMeasuring"
    ),
    "GMW_Insertion": partial(create_gmw_event, event_type="GMW_Insertion"),
    "GMW_TubeStatus": partial(create_gmw_event, event_type="GMW_TubeStatus"),
    "GMW_Lengthening": partial(create_gmw_event, event_type="GMW_Lengthening"),
    "GMW_Shortening": partial(create_gmw_event, event_type="GMW_Shortening"),
    "GMW_ElectrodeStatus": partial(create_gmw_event, event_type="GMW_ElectrodeStatus"),
    "GMW_Maintainer": partial(create_gmw_event, event_type="GMW_Maintainer"),
    "GMW_Removal": create_gmw_removal,
    "GLD_StartRegistration": create_gld,
    "GLD_Addition": create_gld_addition,
    "GMN_StartRegistration": create_gmn,
    "GMN_MeasuringPoint": partial(
        create_gmn_measuringpoint, event_type="GMN_MeasuringPoint"
    ),
    "GMN_MeasuringPointEndDate": partial(
        create_gmn_measuringpoint, event_type="GMN_MeasuringPointEndDate"
    ),
    "GMN_TubeReference": partial(
        create_gmn_measuringpoint, event_type="GMN_TubeReference"
    ),
    "FRD_StartRegistration": create_frd,
    # "GAR": create_gar,  # TODO
}


def create_objects(
    registration_type: str,
    bro_id: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    try:
        CREATE_FUNCTION_MAPPING[registration_type](
            bro_id=bro_id,
            metadata=metadata,
            sourcedocument_data=sourcedocument_data,
            data_owner=data_owner,
        )
    except KeyError:
        logger.info(
            f"Unable to create as there is no function mapped for registration type: {registration_type}."
        )
        return


def empty_strings_to_none(d: dict) -> dict:
    for key, value in d.items():
        if isinstance(value, str) and value.strip() == "":
            d[key] = None
        elif isinstance(value, dict):
            d[key] = empty_strings_to_none(value)
        elif isinstance(value, list):
            d[key] = [
                empty_strings_to_none(v)
                if isinstance(v, dict)
                else (None if v == "" else v)
                for v in value
            ]
    return d


def drop_empty_strings(d: dict) -> dict:  # noqa: C901
    cleaned = {}
    for key, value in d.items():
        if isinstance(value, str):
            if value.strip() == "":
                continue  # skip this field entirely
            cleaned[key] = value
        elif isinstance(value, dict):
            nested = drop_empty_strings(value)
            if nested:  # only keep if not empty
                cleaned[key] = nested
        elif isinstance(value, list):
            cleaned_list = []
            for v in value:
                if isinstance(v, dict):
                    nested = drop_empty_strings(v)
                    if nested:
                        cleaned_list.append(nested)
                elif not (isinstance(v, str) and v.strip() == ""):
                    cleaned_list.append(v)
            if cleaned_list:
                cleaned[key] = cleaned_list
        else:
            cleaned[key] = value
    return cleaned
