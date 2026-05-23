import logging

from gar.models import (
    GAR,
    Analysis,
    AnalysisProcess,
    FieldMeasurement,
    LaboratoryResearch,
)

logger = logging.getLogger(__name__)


def create_gar(
    bro_id: str, metadata: dict, sourcedocument_data: dict, data_owner: str
) -> None:
    """Create a GAR with its field measurements and laboratory research hierarchy."""
    field_research = sourcedocument_data.get("fieldResearch", {})
    field_observation = field_research.get("fieldObservation", {})

    gar, _ = GAR.objects.update_or_create(
        bro_id=bro_id,
        data_owner=data_owner,
        defaults={
            "internal_id": sourcedocument_data.get("objectIdAccountableParty"),
            "delivery_accountable_party": metadata.get("deliveryAccountableParty"),
            "quality_regime": metadata.get("qualityRegime"),
            "quality_control_method": sourcedocument_data.get(
                "qualityControlMethod", "onbekend"
            ),
            "gmw_bro_id": sourcedocument_data.get("gmwBroId"),
            "tube_number": sourcedocument_data.get("tubeNumber"),
            "sampling_datetime": field_research.get("samplingDateTime"),
            "sampling_standard": field_research.get("samplingStandard"),
            "primary_colour": field_research.get("primaryColour"),
            "secondary_colour": field_research.get("secondaryColour"),
            "colour_strength": field_research.get("colourStrength"),
            "pump_type": field_research.get("pumpType"),
            "abnormality_in_cooling": field_observation.get("abnormalityInCooling"),
            "abnormality_in_device": field_observation.get("abnormalityInDevice"),
            "polluted_by_engine": field_observation.get("pollutedByEngine"),
            "filter_aerated": field_observation.get("filterAerated"),
            "groundwater_level_dropped_too_much": field_observation.get(
                "groundwaterLevelDroppedTooMuch"
            ),
            "abnormal_filter": field_observation.get("abnormalFilter"),
            "sample_aerated": field_observation.get("sampleAerated"),
            "hose_reused": field_observation.get("hoseReused"),
            "temperature_difficult_to_measure": field_observation.get(
                "temperatureDifficultToMeasure"
            ),
        },
    )

    _create_field_measurements(gar, field_research, data_owner)
    _create_laboratory_researches(
        gar, sourcedocument_data.get("laboratoryAnalyses", []), data_owner
    )
    logger.info(f"Successfully created/updated GAR bro_id={bro_id}.")


def _create_field_measurements(gar: GAR, field_research: dict, data_owner: str) -> None:
    for measurement in field_research.get("fieldMeasurements", []):
        FieldMeasurement.objects.update_or_create(
            gar=gar,
            parameter=int(measurement.get("parameter")),
            data_owner=data_owner,
            defaults={
                "unit": measurement.get("unit"),
                "field_measurement_value": measurement.get("fieldMeasurementValue"),
                "quality_control_status": measurement.get("qualityControlStatus"),
            },
        )


def _create_laboratory_researches(
    gar: GAR, lab_analyses: list, data_owner: str
) -> None:
    for lab_analysis in lab_analyses:
        lab_research, _ = LaboratoryResearch.objects.update_or_create(
            gar=gar,
            laboratory_kvk_number=lab_analysis.get("responsibleLaboratoryKvk"),
            data_owner=data_owner,
        )
        for process in lab_analysis.get("analysisProcesses", []):
            analysis_process, _ = AnalysisProcess.objects.update_or_create(
                laboratory_research=lab_research,
                analyses_date=process.get("date"),
                data_owner=data_owner,
                defaults={
                    "analytical_technique": process.get("analyticalTechnique"),
                    "validation_method": process.get("valuationMethod"),
                },
            )
            for analysis in process.get("analyses", []):
                Analysis.objects.update_or_create(
                    analysis_process=analysis_process,
                    parameter=int(analysis.get("parameter")),
                    data_owner=data_owner,
                    defaults={
                        "unit": analysis.get("unit"),
                        "value": str(analysis.get("analysisMeasurementValue"))
                        if analysis.get("analysisMeasurementValue") is not None
                        else None,
                        "limit_symbol": analysis.get("limitSymbol"),
                        "reporting_limit": str(analysis.get("reportingLimit"))
                        if analysis.get("reportingLimit") is not None
                        else None,
                        "status_quality_control": analysis.get("qualityControlStatus"),
                    },
                )
