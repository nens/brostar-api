import logging
from functools import partial

from pyproj import Transformer

from frd.models import FRD
from gld.models import GLD
from gmn.models import GMN
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
        },
    )[0]
    for tube in sourcedocument_data.get("monitoringTubes", []):
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
                "screen_top_position": tube.get("screenTopPosition"),
                "screen_bottom_position": tube.get("screenBottomPosition"),
                "plain_tube_part_length": tube.get("plainTubePartLength"),
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
        logger.error(f"GMW not found for bro_id={bro_id}, owner={data_owner}")
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


def find_linked_gmns(gmn_bro_ids: list[str] | str) -> list[GMN]:
    if isinstance(gmn_bro_ids, str):
        gmn_bro_ids = [gmn_bro_ids]
    gmns = GMN.objects.filter(bro_id__in=gmn_bro_ids)
    if len(gmns) != len(gmn_bro_ids):
        found_bro_ids = {gmn.bro_id for gmn in gmns}
        missing = set(gmn_bro_ids) - found_bro_ids
        logger.warning(f"Could not find GMNs with bro_id(s): {', '.join(missing)}")
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
    # "GMW_Removal": create_gmw_removal,
    "GLD_StartRegistration": create_gld,
    # "GLD_Addition": create_gld_addition,
    "GMN_StartRegistration": create_gmn,
    # "GMN_MeasuringPoint": create_gmn_measuringpoint,
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
        logger.warning(
            f"No create function mapped for registration type: {registration_type}. \nNo objects created."
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
