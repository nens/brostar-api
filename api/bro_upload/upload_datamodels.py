import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, field_validator, model_validator

from .type_helpers import (
    BroDomainOptions,
    CorrectionReasonOptions,
    QualityRegimeOptions,
    RegistrationTypeOptions,
    RequestTypeOptions,
)


## Uploadtask models
def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    class Config:
        validate_by_name = True
        extra = "ignore"

        # Ensure aliasing works for all fields with underscores
        @staticmethod
        def alias_generator(field_name: str) -> str:
            return to_camel(field_name)


## Uploadtask models
class UploadTaskMetadata(CamelModel):
    request_reference: str
    delivery_accountable_party: str | None = None
    bro_id: str | None = None
    quality_regime: QualityRegimeOptions
    correction_reason: CorrectionReasonOptions | None = None


class GARBulkUploadMetadata(CamelModel):
    request_reference: str
    quality_regime: str
    delivery_accountable_party: str | None = None
    quality_control_method: str | None = None
    groundwater_monitoring_nets: list[str] = []
    sampling_operator: int | None = None


class GLDBulkUploadMetadata(CamelModel):
    request_reference: str
    quality_regime: str
    delivery_accountable_party: str | None = None
    bro_id: str


class GMNBulkUploadMetadata(CamelModel):
    request_reference: str
    quality_regime: str
    delivery_accountable_party: str | None = None
    bro_id: str


class GLDBulkUploadSourcedocumentData(CamelModel):
    validation_status: str | None = None
    investigator_kvk: str
    observation_type: str
    evaluation_procedure: str
    measurement_instrument_type: str
    process_reference: str
    air_pressure_compensation_type: str | None = None
    begin_position: str | None = None
    end_position: str | None = None
    result_time: str | None = None


# GMN sourcedocs_data
class MeasuringPoint(CamelModel):
    measuring_point_code: str
    bro_id: str
    tube_number: int


class GMNStartregistration(CamelModel):
    object_id_accountable_party: str
    name: str
    delivery_context: str
    monitoring_purpose: str
    groundwater_aspect: str
    start_date_monitoring: str
    measuring_points: list[MeasuringPoint]


class GMNMeasuringPoint(CamelModel):
    event_date: str
    measuring_point_code: str
    bro_id: str
    tube_number: int


class GMNMeasuringPointEndDate(CamelModel):
    event_date: str | None = None
    measuring_point_code: str
    bro_id: str
    tube_number: int


class GMNTubeReference(CamelModel):
    event_date: str
    measuring_point_code: str
    bro_id: str
    tube_number: int


class GMNClosure(CamelModel):
    end_date_monitoring: str


# GMW sourcedocs_data
class Electrode(CamelModel):
    electrode_number: int
    electrode_packing_material: str
    electrode_status: str
    electrode_position: float | None = None


class GeoOhmCable(CamelModel):
    cable_number: int
    electrodes: list[Electrode]


class MonitoringTube(CamelModel):
    tube_number: int
    tube_type: str
    artesian_well_cap_present: str
    sediment_sump_present: str
    number_of_geo_ohm_cables: int = 0
    tube_top_diameter: int | None = None
    variable_diameter: str | None = None
    tube_status: str
    tube_top_position: float
    tube_top_positioning_method: str
    tube_packing_material: str
    tube_material: str
    glue: str
    screen_length: float
    sock_material: str
    plain_tube_part_length: float
    sediment_sump_length: float | None = None
    geo_ohm_cables: list[GeoOhmCable] | None = None

    # Newly added in GMW1.1
    screen_protection: str | None = None


class GMWConstruction(CamelModel):
    object_id_accountable_party: str
    delivery_context: str
    construction_standard: str
    initial_function: str
    number_of_monitoring_tubes: int
    ground_level_stable: str
    nitg_code: str | None = None
    well_stability: str | None = None
    owner: str | None = None
    maintenance_responsible_party: str | None = None
    well_head_protector: str
    well_construction_date: str
    delivered_location: str  # X -7000 to 289000 and Y 289000 629000
    horizontal_positioning_method: str
    local_vertical_reference_point: str = "NAP"
    offset: float = 0.000
    vertical_datum: str = "NAP"
    ground_level_position: float | None = None
    ground_level_positioning_method: str
    monitoring_tubes: list["MonitoringTube"]
    date_to_be_corrected: str | None = None

    # Newly added in GMW1.1
    geometric_data_publicly_available: str | None = None
    is_abroad: str | None = None
    survey: list[str] | None = None


# noqa: N815 - Using mixedCase to match API requirements
class GMWEvent(CamelModel):
    event_date: str


# noqa: N815 - Using mixedCase to match API requirements
class GMWElectrodeStatus(GMWEvent):
    electrodes: list[Electrode]


class GMWGroundLevel(GMWEvent):
    well_stability: str = "stabielNAP"
    ground_level_stable: str = "nee"
    ground_level_position: float
    ground_level_positioning_method: str


class GMWGroundLevelMeasuring(GMWEvent):
    ground_level_position: float
    ground_level_positioning_method: str


class GMWInsertionTube(CamelModel):
    tube_number: int
    tube_top_position: float
    tube_top_positioning_method: str
    inserted_part_length: float
    inserted_part_diameter: int
    inserted_part_material: str


class GMWInsertion(GMWEvent):
    monitoring_tubes = list[GMWInsertionTube]


class MonitoringTubeLengthening(CamelModel):
    tube_number: int
    variable_diameter: str | None = None
    tube_top_diameter: int | None = None
    tube_top_position: float
    tube_top_positioning_method: str
    tube_material: str | None = None
    glue: str | None = None
    plain_tube_part_length: float


class GMWLengthening(GMWEvent):
    well_head_protector: str | None = None
    monitoring_tubes: list[MonitoringTubeLengthening]


class GMWMaintainer(GMWEvent):
    maintenance_responsible_party: str


class GMWOwner(GMWEvent):
    owner: str


class MonitoringTubePositions(CamelModel):
    tube_number: int
    tube_top_position: float
    tube_top_positioning_method: str


class GMWPositions(GMWEvent):
    well_stability: str = "nee"
    ground_level_stable: str = "instabiel"
    ground_level_position: float
    ground_level_positioning_method: str
    monitoring_tubes: list[MonitoringTubePositions]


class GMWPositionsMeasuring(GMWEvent):
    monitoring_tubes: list[MonitoringTubePositions]
    ground_level_position: float | None = None
    ground_level_positioning_method: str | None = None


class GMWRemoval(GMWEvent):
    pass


class GMWShift(GMWEvent):
    ground_level_position: float
    ground_level_positioning_method: str


class MonitoringTubeShortening(CamelModel):
    tube_number: int
    tube_top_position: float
    tube_top_positioning_method: str
    plain_tube_part_length: float


class GMWShortening(GMWEvent):
    well_head_protector: str | None = None
    monitoring_tubes: list[MonitoringTubeShortening]


class MonitoringTubeStatus(CamelModel):
    tube_number: int
    tube_status: str


class GMWTubeStatus(GMWEvent):
    monitoring_tubes: list[MonitoringTubeStatus]


class GMWWellHeadProtector(GMWEvent):
    well_head_protector: str


class GMWAdditionalSurvey(GMWEvent):
    bro_id: str
    survey_type: Literal["BHR", "CPT"]


class FieldMeasurement(CamelModel):
    parameter: int
    unit: str
    field_measurement_value: float
    quality_control_status: str


class FieldResearch(CamelModel):
    sampling_date_time: str | datetime
    sampling_operator: str | None = None
    sampling_standard: str = "onbekend"
    pump_type: str = "onbekend"
    primary_colour: str | None = None
    secondary_colour: str | None = None
    colour_strength: str | None = None
    abnormality_in_cooling: str = "onbekend"
    abnormality_in_device: str = "onbekend"
    polluted_by_engine: str = "onbekend"
    filter_aerated: str = "onbekend"
    ground_water_level_dropped_too_much: str = "onbekend"
    abnormal_filter: str = "onbekend"
    sample_aerated: str = "onbekend"
    hose_reused: str = "onbekend"
    temperature_difficult_to_measure: str = "onbekend"
    field_measurements: list[FieldMeasurement] | None = None

    @field_validator("sampling_date_time", mode="before")
    def format_datetime(cls, value):
        if isinstance(value, datetime):
            return value.isoformat(sep="T", timespec="seconds")
        return value


class Analysis(CamelModel):
    parameter: str | int
    unit: str
    analysis_measurement_value: float
    limit_symbol: str | None = None
    reporting_limit: str | float | None = None
    quality_control_status: str


class AnalysisProcess(CamelModel):
    date: str | date
    analytical_technique: str
    valuation_method: str
    analyses: list[Analysis]

    @field_validator("date", mode="before")
    def format_date(cls, value):
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        return value


class LaboratoryAnalysis(CamelModel):
    responsible_laboratory_kvk: str | None = None
    analysis_processes: list[AnalysisProcess] = []


class GAR(CamelModel):
    object_id_accountable_party: str
    quality_control_method: str = "onbekend"  # Beoordelingsprocedure
    groundwater_monitoring_nets: list[str] = []
    gmw_bro_id: str
    tube_number: str | int
    field_research: FieldResearch
    laboratory_analyses: list[LaboratoryAnalysis] = []


class GLDStartregistration(CamelModel):
    object_id_accountable_party: str | None = None
    groundwater_monitoring_nets: list[str] = []
    gmw_bro_id: str
    tube_number: str | int


class TimeValuePair(CamelModel):
    time: str
    value: float | None = None
    status_quality_control: str = "onbekend"
    censor_reason: str | None = None
    censoring_limitvalue: float | None = None

    @field_validator("time", mode="before")
    def format_datetime(cls, value):
        if isinstance(value, datetime):
            return value.isoformat(sep="T", timespec="seconds")
        return value

    @field_validator("value", "censoring_limitvalue", mode="before")
    def parse_comma_decimal(cls, value):
        """Convert strings like '1,32' or '-0,5' into floats."""
        if isinstance(value, str):
            value = value.strip()
            if value == "" or value.lower() == "null":
                return None
            # Replace comma with dot if needed
            value = value.replace(",", ".")
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"Invalid numeric value: {value!r}")
        return value


class GLDAddition(CamelModel):
    date: str | None = None
    observation_id: str | None = None
    observation_process_id: str | None = None
    measurement_timeseries_id: str | None = None
    validation_status: str | None = None
    investigator_kvk: str
    observation_type: str
    evaluation_procedure: str
    measurement_instrument_type: str
    process_reference: str
    air_pressure_compensation_type: str | None = None
    begin_position: str
    end_position: str
    result_time: str | None = None
    time_value_pairs: list[TimeValuePair]

    @model_validator(mode="before")
    def generate_missing_ids(cls, data):
        if isinstance(data, dict):
            if not data.get("observation_id"):
                data["observation_id"] = f"_{uuid.uuid4()}"

            if not data.get("observation_process_id"):
                data["observation_process_id"] = f"_{uuid.uuid4()}"

            if not data.get("measurement_timeseries_id"):
                data["measurement_timeseries_id"] = f"_{uuid.uuid4()}"

            # Handle validation status
            if data.get("observation_type") == "reguliereMeting" and not data.get(
                "validation_status"
            ):
                data["validation_status"] = "onbekend"
            elif data.get("observation_type") == "controlemeting":
                data["validation_status"] = None

        return data

    @model_validator(mode="after")
    def correct_air_pressure_compensation_type(cls, model):
        if model.measurement_instrument_type not in ["druksensor", "stereoDruksensor"]:
            model.air_pressure_compensation_type = None

        if model.air_pressure_compensation_type in ["", "None"]:
            model.air_pressure_compensation_type = None

        return model


class GLDClosure(CamelModel):
    event_date: str


class FRDStartRegistration(CamelModel):
    object_id_accountable_party: str | None = None
    groundwater_monitoring_nets: list[str] = []
    gmw_bro_id: str
    tube_number: int


class MeasurementConfiguration(CamelModel):
    measurement_configuration_id: str
    measurement_e1_cable_number: int
    measurement_e1_electrode_number: int
    measurement_e2_cable_number: int
    measurement_e2_electrode_number: int
    current_e1_cable_number: int
    current_e1_electrode_number: int
    current_e2_cable_number: int
    current_e2_electrode_number: int


class FRDGemMeasurementConfiguration(CamelModel):
    measurement_configurations: list[MeasurementConfiguration]


class FRDEmmInstrumentConfiguration(CamelModel):
    instrument_configuration_id: str
    relative_position_transmitter_coil: str | int
    relative_position_primary_receiver_coil: str | int
    secondary_receiver_coil_available: str
    relative_position_secondary_receiver_coil: str | int | None = None
    coil_frequency_known: str
    coil_frequency: int | None = None
    instrument_length: int


class FRDEmmMeasurement(CamelModel):
    measurement_date: date | str
    measurement_operator_kvk: str
    determination_procedure: str
    measurement_evaluation_procedure: str
    measurement_series_count: int
    measurement_series_values: str
    related_instrument_configuration_id: str
    calculation_operator_kvk: str
    calculation_evaluation_procedure: str
    calculation_count: int
    calculation_values: str


class GemMeasurement(CamelModel):
    value: float
    unit: str = "Ohm"
    configuration: str


class RelatedCalculatedApparentFormationResistance(CamelModel):
    calculation_operator_kvk: str
    evaluation_procedure: str
    element_count: int
    values: str


class FRDGemMeasurement(CamelModel):
    measurement_date: str | date
    measurement_operator_kvk: str
    determination_procedure: str
    evaluation_procedure: str
    measurements: list[GemMeasurement]
    related_calculated_apparent_formation_resistance: (
        RelatedCalculatedApparentFormationResistance | None
    ) = None


class UploadTask(BaseModel):
    bro_domain: BroDomainOptions
    project_number: str
    registration_type: RegistrationTypeOptions
    request_type: RequestTypeOptions
    sourcedocument_data: Any
    metadata: UploadTaskMetadata
