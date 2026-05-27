import logging

from frd.models import (
    FRD,
    CalculatedApparentFormationResistance,
    GeoElectricMeasure,
    GeoElectricMeasurement,
    MeasurementConfiguration,
)

logger = logging.getLogger(__name__)


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


def create_frd_gem_measurement_configuration(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    """Create GEM MeasurementConfiguration records for an FRD."""
    try:
        frd = FRD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except FRD.DoesNotExist:
        logger.info(f"FRD not found for bro_id={bro_id}, owner={data_owner}")
        return

    for config in sourcedocument_data.get("measurementConfigurations", []):
        measurement_pair = {
            "measurementE1CableNumber": config.get("measurementE1CableNumber"),
            "measurementE1ElectrodeNumber": config.get("measurementE1ElectrodeNumber"),
            "measurementE2CableNumber": config.get("measurementE2CableNumber"),
            "measurementE2ElectrodeNumber": config.get("measurementE2ElectrodeNumber"),
        }
        current_pair = {
            "currentE1CableNumber": config.get("currentE1CableNumber"),
            "currentE1ElectrodeNumber": config.get("currentE1ElectrodeNumber"),
            "currentE2CableNumber": config.get("currentE2CableNumber"),
            "currentE2ElectrodeNumber": config.get("currentE2ElectrodeNumber"),
        }
        MeasurementConfiguration.objects.update_or_create(
            frd=frd,
            measurement_configuration_id=config.get("measurementConfigurationId"),
            data_owner=data_owner,
            defaults={
                "measurement_pair": measurement_pair,
                "current_pair": current_pair,
            },
        )
    logger.info(f"Created/updated measurement configurations for FRD bro_id={bro_id}.")


def create_frd_emm_instrument_configuration(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    """Create EMM InstrumentConfiguration record for an FRD.

    EMM instrument configurations are stored in the MeasurementConfiguration model
    with instrument-specific fields packed into measurement_pair.
    """
    try:
        frd = FRD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except FRD.DoesNotExist:
        logger.info(f"FRD not found for bro_id={bro_id}, owner={data_owner}")
        return

    instrument_data = {
        "relativePositionTransmitterCoil": sourcedocument_data.get(
            "relativePositionTransmitterCoil"
        ),
        "relativePositionPrimaryReceiverCoil": sourcedocument_data.get(
            "relativePositionPrimaryReceiverCoil"
        ),
        "secondaryReceiverCoilAvailable": sourcedocument_data.get(
            "secondaryReceiverCoilAvailable"
        ),
        "relativePositionSecondaryReceiverCoil": sourcedocument_data.get(
            "relativePositionSecondaryReceiverCoil"
        ),
        "coilFrequencyKnown": sourcedocument_data.get("coilFrequencyKnown"),
        "coilFrequency": sourcedocument_data.get("coilFrequency"),
        "instrumentLength": sourcedocument_data.get("instrumentLength"),
    }
    MeasurementConfiguration.objects.update_or_create(
        frd=frd,
        measurement_configuration_id=sourcedocument_data.get(
            "instrumentConfigurationId"
        ),
        data_owner=data_owner,
        defaults={
            "measurement_pair": instrument_data,
            "current_pair": None,
        },
    )
    logger.info(
        f"Created/updated EMM instrument configuration for FRD bro_id={bro_id}."
    )


def create_frd_gem_measurement(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    """Create a GeoElectricMeasurement with its measures and optional calculated resistance."""
    try:
        frd = FRD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except FRD.DoesNotExist:
        logger.info(f"FRD not found for bro_id={bro_id}, owner={data_owner}")
        return

    gem, _ = GeoElectricMeasurement.objects.update_or_create(
        frd=frd,
        measurement_date=sourcedocument_data.get("measurementDate"),
        data_owner=data_owner,
        defaults={
            "determination_procedure": sourcedocument_data.get(
                "determinationProcedure"
            ),
            "evaluation_procedure": sourcedocument_data.get("evaluationProcedure"),
        },
    )

    # Recreate sub-measures on every registration to keep them in sync
    gem.measures.all().delete()
    for measure in sourcedocument_data.get("measurements", []):
        GeoElectricMeasure.objects.create(
            geo_electric_measurement=gem,
            resistance=str(measure.get("value"))
            if measure.get("value") is not None
            else None,
            related_measurement_configuration=measure.get("configuration"),
            data_owner=data_owner,
        )

    calc_resistance = sourcedocument_data.get(
        "relatedCalculatedApparentFormationResistance"
    )
    if calc_resistance:
        CalculatedApparentFormationResistance.objects.update_or_create(
            geo_electric_measurement=gem,
            defaults={
                "evaluation_procedure": calc_resistance.get("evaluationProcedure"),
                "values": calc_resistance.get("values"),
                "data_owner": data_owner,
            },
        )

    logger.info(
        f"Created/updated GEM measurement for FRD bro_id={bro_id}, date={sourcedocument_data.get('measurementDate')}."
    )


def create_frd_emm_measurement(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    """Create an EMM (Electro Magnetic Method) measurement for an FRD.

    EMM measurements are stored in the same GeoElectricMeasurement model as GEM.
    The calculated series values are stored in CalculatedApparentFormationResistance.
    """
    try:
        frd = FRD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except FRD.DoesNotExist:
        logger.info(f"FRD not found for bro_id={bro_id}, owner={data_owner}")
        return

    gem, _ = GeoElectricMeasurement.objects.update_or_create(
        frd=frd,
        measurement_date=sourcedocument_data.get("measurementDate"),
        data_owner=data_owner,
        defaults={
            "determination_procedure": sourcedocument_data.get(
                "determinationProcedure"
            ),
            "evaluation_procedure": sourcedocument_data.get(
                "measurementEvaluationProcedure"
            ),
        },
    )

    CalculatedApparentFormationResistance.objects.update_or_create(
        geo_electric_measurement=gem,
        defaults={
            "evaluation_procedure": sourcedocument_data.get(
                "calculationEvaluationProcedure"
            ),
            "values": sourcedocument_data.get("calculationValues"),
            "data_owner": data_owner,
        },
    )

    logger.info(
        f"Created/updated EMM measurement for FRD bro_id={bro_id}, date={sourcedocument_data.get('measurementDate')}."
    )


# ── Update functions ──────────────────────────────────────────────────────────


def update_frd(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    try:
        frd = FRD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except FRD.DoesNotExist:
        logger.info(f"FRD not found for bro_id={bro_id}, owner={data_owner}")
        return

    source_field_map = {
        "internal_id": "objectIdAccountableParty",
        "delivery_accountable_party": "deliveryAccountableParty",
        "gmw_bro_id": "gmwBroId",
        "tube_number": "tubeNumber",
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
        setattr(frd, field, value)
    if updates:
        frd.save(update_fields=list(updates.keys()))


# ── Delete functions ──────────────────────────────────────────────────────────


def delete_frd_measurement_configuration(
    bro_id: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    try:
        frd = FRD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except FRD.DoesNotExist:
        logger.info(f"FRD not found for bro_id={bro_id}, owner={data_owner}")
        return

    config_id = sourcedocument_data.get("measurementConfigurationId")
    config_qs = MeasurementConfiguration.objects.filter(frd=frd, data_owner=data_owner)
    if config_id:
        config_qs = config_qs.filter(measurement_configuration_id=config_id)

    deleted_count, _ = config_qs.delete()
    logger.info(
        f"Deleted {deleted_count} measurement configuration(s) for bro_id={bro_id}."
    )


def delete_frd_measurement(
    bro_id: str,
    metadata: dict,
    sourcedocument_data: dict,
    data_owner: str,
) -> None:
    try:
        frd = FRD.objects.get(bro_id=bro_id, data_owner=data_owner)
    except FRD.DoesNotExist:
        logger.info(f"FRD not found for bro_id={bro_id}, owner={data_owner}")
        return

    date_to_correct = sourcedocument_data.get("dateToBeCorrected")
    measurement_qs = GeoElectricMeasurement.objects.filter(
        frd=frd, data_owner=data_owner
    )
    if date_to_correct:
        measurement_qs = measurement_qs.filter(measurement_date=date_to_correct)

    deleted_count, _ = measurement_qs.delete()
    logger.info(
        f"Deleted {deleted_count} geo-electric measurement(s) for bro_id={bro_id}, date={date_to_correct}."
    )
