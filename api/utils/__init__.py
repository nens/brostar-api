"""
api.utils package — domain-specific create/update/delete utilities.

Each sub-module owns one BRO domain.  This __init__.py re-exports every
symbol that was previously in the flat api/utils.py so that existing
imports continue to work without change.
"""

import logging as _logging
from functools import partial

from .frd_utils import (
    create_frd,
    create_frd_emm_instrument_configuration,
    create_frd_emm_measurement,
    create_frd_gem_measurement,
    create_frd_gem_measurement_configuration,
    delete_frd_measurement,
    delete_frd_measurement_configuration,
    update_frd,
)
from .gar_utils import create_gar
from .gld_utils import (
    create_gld,
    create_gld_addition,
    delete_gld_observation,
    update_gld,
    update_gld_observation,
)
from .gmn_utils import (
    create_gmn,
    create_gmn_measuringpoint,
    delete_gmn_intermediate_event,
    find_linked_gmns,
    remove_enddate_gmn,
    update_enddate_gmn,
    update_gmn,
    update_gmn_measuringpoint,
)
from .gmw_utils import (
    create_gmw,
    create_gmw_event,
    create_gmw_removal,
    update_gmw,
    update_gmw_event,
    update_gmw_removal,
)
from .gpd_utils import create_gpd, create_gpd_report
from .guf_utils import create_guf
from .helpers import (
    drop_empty_strings,
    empty_strings_to_none,
    strip_whitespace,
    transformer,
)

__all__ = [
    # helpers
    "transformer",
    "empty_strings_to_none",
    "strip_whitespace",
    "drop_empty_strings",
    # GMW
    "create_gmw",
    "create_gmw_event",
    "create_gmw_removal",
    "update_gmw",
    "update_gmw_event",
    "update_gmw_removal",
    # GLD
    "create_gld",
    "create_gld_addition",
    "update_gld",
    "update_gld_observation",
    "delete_gld_observation",
    # GMN
    "find_linked_gmns",
    "create_gmn",
    "create_gmn_measuringpoint",
    "update_gmn",
    "update_gmn_measuringpoint",
    "delete_gmn_intermediate_event",
    # FRD
    "create_frd",
    "create_frd_gem_measurement_configuration",
    "create_frd_emm_instrument_configuration",
    "create_frd_gem_measurement",
    "create_frd_emm_measurement",
    "update_frd",
    "delete_frd_measurement_configuration",
    "delete_frd_measurement",
    # GAR
    "create_gar",
    # GUF
    "create_guf",
    # GPD
    "create_gpd",
    "create_gpd_report",
    # mappings + dispatchers
    "CREATE_FUNCTION_MAPPING",
    "UPDATE_FUNCTION_MAPPING",
    "DELETE_FUNCTION_MAPPING",
    "create_objects",
    "update_objects",
    "delete_objects",
]

# ── Mappings ──────────────────────────────────────────────────────────────────

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
    "GMN_Closure": update_enddate_gmn,
    "FRD_StartRegistration": create_frd,
    "FRD_GEM_MeasurementConfiguration": create_frd_gem_measurement_configuration,
    "FRD_EMM_InstrumentConfiguration": create_frd_emm_instrument_configuration,
    "FRD_GEM_Measurement": create_frd_gem_measurement,
    "FRD_EMM_Measurement": create_frd_emm_measurement,
    "GAR_StartRegistration": create_gar,
    "GUF_StartRegistration": create_guf,
    "GPD_StartRegistration": create_gpd,
    "GPD_AddReport": create_gpd_report,
}

UPDATE_FUNCTION_MAPPING = {
    "GMW_Construction": update_gmw,
    "GMW_Positions": partial(update_gmw_event, event_type="GMW_Positions"),
    "GMW_PositionsMeasuring": partial(
        update_gmw_event, event_type="GMW_PositionsMeasuring"
    ),
    "GMW_WellHeadProtector": partial(
        update_gmw_event, event_type="GMW_WellHeadProtector"
    ),
    "GMW_Owner": partial(update_gmw_event, event_type="GMW_Owner"),
    "GMW_Shift": partial(update_gmw_event, event_type="GMW_Shift"),
    "GMW_GroundLevel": partial(update_gmw_event, event_type="GMW_GroundLevel"),
    "GMW_GroundLevelMeasuring": partial(
        update_gmw_event, event_type="GMW_GroundLevelMeasuring"
    ),
    "GMW_Insertion": partial(update_gmw_event, event_type="GMW_Insertion"),
    "GMW_TubeStatus": partial(update_gmw_event, event_type="GMW_TubeStatus"),
    "GMW_Lengthening": partial(update_gmw_event, event_type="GMW_Lengthening"),
    "GMW_Shortening": partial(update_gmw_event, event_type="GMW_Shortening"),
    "GMW_ElectrodeStatus": partial(update_gmw_event, event_type="GMW_ElectrodeStatus"),
    "GMW_Maintainer": partial(update_gmw_event, event_type="GMW_Maintainer"),
    "GMW_Removal": update_gmw_removal,
    "GLD_StartRegistration": update_gld,
    "GLD_Addition": update_gld_observation,
    "GMN_StartRegistration": update_gmn,
    "GMN_MeasuringPoint": partial(
        update_gmn_measuringpoint, event_type="GMN_MeasuringPoint"
    ),
    "GMN_MeasuringPointEndDate": partial(
        update_gmn_measuringpoint, event_type="GMN_MeasuringPointEndDate"
    ),
    "GMN_TubeReference": partial(
        update_gmn_measuringpoint, event_type="GMN_TubeReference"
    ),
    "FRD_StartRegistration": update_frd,
}

DELETE_FUNCTION_MAPPING = {
    "GLD_Addition": delete_gld_observation,
    "GMN_MeasuringPoint": delete_gmn_intermediate_event,
    "GMN_MeasuringPointEndDate": delete_gmn_intermediate_event,
    "GMN_TubeReference": delete_gmn_intermediate_event,
    "GMN_Closure": remove_enddate_gmn,
    "FRD_GEM_MeasurementConfiguration": delete_frd_measurement_configuration,
    "FRD_GEM_Measurement": delete_frd_measurement,
    "FRD_EMM_InstrumentConfiguration": delete_frd_measurement_configuration,
    "FRD_EMM_Measurement": delete_frd_measurement,
}


# ── Dispatcher functions ──────────────────────────────────────────────────────
_logger = _logging.getLogger(__name__)


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
        _logger.info(
            f"Unable to create as there is no function mapped for registration type: {registration_type}."
        )
        return


def update_objects(
    registration_type: str,
    bro_id: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    try:
        UPDATE_FUNCTION_MAPPING[registration_type](
            bro_id=bro_id,
            metadata=metadata,
            sourcedocument_data=sourcedocument_data,
            data_owner=data_owner,
        )
    except KeyError:
        _logger.info(
            f"Unable to update as there is no function mapped for registration type: {registration_type}."
        )
        return


def delete_objects(
    registration_type: str,
    bro_id: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    try:
        DELETE_FUNCTION_MAPPING[registration_type](
            bro_id=bro_id,
            metadata=metadata,
            sourcedocument_data=sourcedocument_data,
            data_owner=data_owner,
        )
    except KeyError:
        _logger.info(
            f"Unable to delete as there is no function mapped for registration type: {registration_type}."
        )
        return
