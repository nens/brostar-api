import datetime
import logging

from guf.models import (
    GUF,
    DesignInstallation,
    DesignLoop,
    DesignSurfaceInfiltration,
    DesignWell,
    EnergyCharacteristics,
)

logger = logging.getLogger(__name__)


def _parse_flexible_date(date_str: str | None) -> datetime.date | None:
    """Parse BRO dates with flexible granularity: YYYY-MM-DD, YYYY-MM, or YYYY."""
    if not date_str:
        return None
    try:
        if len(date_str) == 4:  # YYYY
            return datetime.date(int(date_str), 1, 1)
        elif len(date_str) == 7:  # YYYY-MM
            year, month = date_str.split("-")
            return datetime.date(int(year), int(month), 1)
        else:  # YYYY-MM-DD
            return datetime.date.fromisoformat(date_str)
    except (ValueError, AttributeError):
        return None


def create_guf(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    """Create a GUF with its design installations and all nested sub-records."""
    guf, _ = GUF.objects.update_or_create(
        bro_id=bro_id,
        data_owner=data_owner,
        defaults={
            "internal_id": sourcedocument_data.get("objectIdAccountableParty"),
            "delivery_accountable_party": metadata.get("deliveryAccountableParty"),
            "quality_regime": metadata.get("qualityRegime"),
            "delivery_context": sourcedocument_data.get("deliveryContext"),
            "start_time": _parse_flexible_date(sourcedocument_data.get("startTime")),
            "identification_licence": sourcedocument_data.get("identificationLicence"),
            "legal_type": sourcedocument_data.get("legalType"),
            "primary_usage_type": sourcedocument_data.get("primaryUsageType"),
            "secondary_usage_types": sourcedocument_data.get("secondaryUsageTypes", []),
            "human_consumption": sourcedocument_data.get("humanConsumption"),
            "licensed_quantities": sourcedocument_data.get("licensedQuantities", []),
        },
    )

    for installation_data in sourcedocument_data.get("designInstallations", []):
        _create_design_installation(guf, installation_data, data_owner)

    logger.info(f"Successfully created/updated GUF bro_id={bro_id}.")


def _create_design_installation(
    guf: GUF, installation_data: dict, data_owner: str
) -> None:
    installation, _ = DesignInstallation.objects.update_or_create(
        guf=guf,
        design_installation_id=installation_data.get("designInstallationId"),
        data_owner=data_owner,
        defaults={
            "installation_function": installation_data.get("installationFunction"),
            "design_installation_pos": installation_data.get("designInstallationPos"),
            "licensed_quantities": installation_data.get("licensedQuantities", []),
        },
    )

    energy_data = installation_data.get("energyCharacteristics")
    if energy_data:
        EnergyCharacteristics.objects.update_or_create(
            installation=installation,
            defaults={
                "energy_cold": str(energy_data.get("energyCold"))
                if energy_data.get("energyCold") is not None
                else None,
                "energy_warm": str(energy_data.get("energyWarm"))
                if energy_data.get("energyWarm") is not None
                else None,
                "maximum_infiltration_temperature_warm": str(
                    energy_data.get("maximumInfiltrationTemperatureWarm")
                )
                if energy_data.get("maximumInfiltrationTemperatureWarm") is not None
                else None,
                "average_infiltration_temperature_cold": str(
                    energy_data.get("averageInfiltrationTemperatureCold")
                )
                if energy_data.get("averageInfiltrationTemperatureCold") is not None
                else None,
                "average_infiltration_temperature_warm": str(
                    energy_data.get("averageInfiltrationTemperatureWarm")
                )
                if energy_data.get("averageInfiltrationTemperatureWarm") is not None
                else None,
                "power_cold": str(energy_data.get("powerCold"))
                if energy_data.get("powerCold") is not None
                else None,
                "power_warm": str(energy_data.get("powerWarm"))
                if energy_data.get("powerWarm") is not None
                else None,
                "power": str(energy_data.get("power"))
                if energy_data.get("power") is not None
                else None,
                "average_warm_water": str(energy_data.get("averageWarmWater"))
                if energy_data.get("averageWarmWater") is not None
                else None,
                "average_cold_water": str(energy_data.get("averageColdWater"))
                if energy_data.get("averageColdWater") is not None
                else None,
                "maximum_year_quantity_warm": str(
                    energy_data.get("maximumYearQuantityWarm")
                )
                if energy_data.get("maximumYearQuantityWarm") is not None
                else None,
                "maximum_year_quantity_cold": str(
                    energy_data.get("maximumYearQuantityCold")
                )
                if energy_data.get("maximumYearQuantityCold") is not None
                else None,
                "data_owner": installation.data_owner,
            },
        )

    for loop_data in installation_data.get("designLoops", []):
        DesignLoop.objects.update_or_create(
            installation=installation,
            design_loop_id=loop_data.get("designLoopId"),
            data_owner=data_owner,
            defaults={
                "loop_type": loop_data.get("loopType"),
                "start_date": _parse_flexible_date(loop_data.get("startDate")),
                "end_date": _parse_flexible_date(loop_data.get("endDate")),
                "geometry_type": loop_data.get("geometryType"),
                "design_loop_pos": loop_data.get("designLoopPos"),
            },
        )

    for well_data in installation_data.get("designWells", []):
        DesignWell.objects.update_or_create(
            installation=installation,
            design_well_id=well_data.get("designWellId"),
            data_owner=data_owner,
            defaults={
                "well_functions": well_data.get("wellFunctions", []),
                "height": str(well_data.get("height"))
                if well_data.get("height") is not None
                else None,
                "well_pos": well_data.get("wellPos"),
                "geometry_publicly_available": well_data.get(
                    "geometryPubliclyAvailable"
                ),
                "maximum_well_depth": str(well_data.get("maximumWellDepth"))
                if well_data.get("maximumWellDepth") is not None
                else None,
                "maximum_well_depth_publicly_available": well_data.get(
                    "maximumWellDepthPubliclyAvailable"
                ),
                "maximum_well_capacity": str(well_data.get("maximumWellCapacity"))
                if well_data.get("maximumWellCapacity") is not None
                else None,
                "relative_temperature": well_data.get("relativeTemperature"),
                "design_screen": well_data.get("designScreen") or {},
            },
        )

    for infiltration_data in installation_data.get("designSurfaceInfiltrations", []):
        DesignSurfaceInfiltration.objects.update_or_create(
            installation=installation,
            design_surface_infiltration_id=infiltration_data.get(
                "designSurfaceInfiltrationId"
            ),
            data_owner=data_owner,
            defaults={
                "design_surface_infiltration_pos": infiltration_data.get(
                    "designSurfaceInfiltrationPos"
                ),
            },
        )
