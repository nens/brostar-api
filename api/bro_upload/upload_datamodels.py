import uuid
from datetime import date, datetime

from pydantic import BaseModel, validator

## Uploadtask models


# Upload task metadata
class UploadTaskMetadata(BaseModel):
    requestReference: str
    deliveryAccountableParty: str | None = None
    qualityRegime: str
    broId: str | None = None
    underPrivilege: str | None = None
    correctionReason: str | None = None
    dateToBeCorrected: str | date | None = None


class GARBulkUploadMetadata(BaseModel):
    requestReference: str
    qualityRegime: str
    deliveryAccountableParty: str | None = None
    qualityControlMethod: str | None = None  # options: https://docs.geostandaarden.nl/bro/def-im-gar-20230607/#detail_class_Model_Beoordelingsprocedure
    groundwaterMonitoringNets: list[str] | None = None
    samplingOperator: str | int | None = None


# GMN sourcedocs_data
class MeasuringPoint(BaseModel):
    measuringPointCode: str
    broId: str
    tubeNumber: str | int


class GMNStartregistration(BaseModel):
    objectIdAccountableParty: str
    name: str
    deliveryContext: str
    monitoringPurpose: str
    groundwaterAspect: str
    startDateMonitoring: str
    measuringPoints: list[MeasuringPoint]


class GMNMeasuringPoint(BaseModel):
    eventDate: str
    measuringPointCode: str
    broId: str
    tubeNumber: str | int


class GMNMeasuringPointEndDate(BaseModel):
    eventDate: str | None = None
    yearMonth: str | None = None
    year: str | None = None
    voidReason: str | None = None
    measuringPointCode: str
    broId: str
    tubeNumber: str | int


class GMNTubeReference(BaseModel):
    eventDate: str
    measuringPointCode: str


class GMNClosure(BaseModel):
    endDateMonitoring: str


# GMW sourcedocs_data
class Electrode(BaseModel):
    electrodeNumber: str | int
    electrodePackingMaterial: str
    electrodeStatus: str
    electrodePosition: str | float


class GeoOhmCable(BaseModel):
    cableNumber: str | int
    electrodes: list[Electrode]


class MonitoringTube(BaseModel):
    tubeNumber: str | int
    tubeType: str
    artesianWellCapPresent: str
    sedimentSumpPresent: str
    numberOfGeoOhmCables: str | int  # Should this not be derived from 'geoohmcables'
    tubeTopDiameter: str | float | None = None
    variableDiameter: str | float
    tubeStatus: str
    tubeTopPosition: str | float
    tubeTopPositioningMethod: str
    tubePackingMaterial: str
    tubeMaterial: str
    glue: str
    screenLength: str | float
    screenProtection: str | None = None
    sockMaterial: str
    plainTubePartLength: str | float
    sedimentSumpLength: str | float | None = None
    geoOhmCables: list[GeoOhmCable] | None = None


class GMWConstruction(BaseModel):
    objectIdAccountableParty: str
    deliveryContext: str
    constructionStandard: str
    initialFunction: str
    numberOfMonitoringTubes: str | int  # Should this not be derived from 'monitoringTubes'
    groundLevelStable: str
    wellStability: str | None = None
    owner: str | None = None
    maintenanceResponsibleParty: str | None = None
    wellHeadProtector: str
    wellConstructionDate: str
    deliveredLocation: str
    horizontalPositioningMethod: str
    localVerticalReferencePoint: str
    offset: str | float
    verticalDatum: str
    groundLevelPosition: str | float | None = None
    groundLevelPositioningMethod: str
    monitoringTubes: list[MonitoringTube]


class GMWEvent(BaseModel):
    eventDate: str


class GMWElectrodeStatus(GMWEvent):
    electrodes: list[Electrode]


class GMWGroundLevel(GMWEvent):
    wellStability: str | None = None
    groundLevelStable: str
    groundLevelPosition: str
    groundLevelPositioningMethod: str


class GMWGroundLevelMeasuring(GMWEvent):
    groundLevelPosition: str
    groundLevelPositioningMethod: str


class GMWInsertion(GMWEvent):
    tubeNumber: str
    tubeTopPosition: str
    tubeTopPositioningMethod: str
    insertedPartLength: str
    insertedPartDiameter: str
    insertedPartMaterial: str


class MonitoringTubeLengthening(BaseModel):
    tubeNumber: str | int
    variableDiameter: str | float
    tubeTopPosition: str | float
    tubeTopPositioningMethod: str
    tubeMaterial: str
    glue: str
    plainTubePartLength: str | float


class GMWLengthening(GMWEvent):
    wellHeadProtector: str | None = None
    monitoringTubes: list[MonitoringTubeLengthening]


class GMWMaintainer(GMWEvent):
    maintenanceResponsibleParty: str


class GMWOwner(GMWEvent):
    owner: str


class MonitoringTubePositions(BaseModel):
    tubeNumber: str | int
    tubeTopPosition: str | float
    tubeTopPositioningMethod: str


class GMWPositions(GMWEvent):
    wellStability: str | None = None
    groundLevelStable: str
    groundLevelPosition: str
    groundLevelPositioningMethod: str
    monitoringTubes: list[MonitoringTubePositions]


class GMWPositionsMeasuring(GMWEvent):
    monitoringTubes: list[MonitoringTube]
    groundLevelPosition: str | None = None
    groundLevelPositioningMethod: str | None = None


class GMWRemoval(GMWEvent):
    pass


class GMWShift(GMWEvent):
    groundLevelPosition: str
    groundLevelPositioningMethod: str


class MonitoringTubeShortening(BaseModel):
    tubeNumber: str | int
    tubeTopPosition: str | float
    tubeTopPositioningMethod: str
    plainTubePartLength: str | float


class GMWShortening(GMWEvent):
    wellHeadProtector: str | None = None
    monitoringTubes: list[MonitoringTubeShortening]


class MonitoringTubeStatus(BaseModel):
    tubeNumber: str | int
    tubeStatus: str


class GMWTubeStatus(GMWEvent):
    monitoringTubes: list[MonitoringTubeStatus]


class GMWWellHeadProtector(GMWEvent):
    wellHeadProtector: str


# GAR sourcedocs_data
class FieldMeasurement(BaseModel):
    parameter: str | int
    unit: str
    fieldMeasurementValue: str | float
    qualityControlStatus: str


class FieldResearch(BaseModel):
    samplingDateTime: str | datetime
    samplingOperator: str | None = None
    samplingStandard: str
    pumpType: str
    primaryColour: str | None = None
    secondaryColour: str | None = None
    colourStrength: str | None = None
    abnormalityInCooling: str
    abnormalityInDevice: str
    pollutedByEngine: str
    filterAerated: str
    groundWaterLevelDroppedTooMuch: str
    abnormalFilter: str
    sampleAerated: str
    hoseReused: str
    temperatureDifficultToMeasure: str
    fieldMeasurements: list[FieldMeasurement] | None = None

    @validator("samplingDateTime", pre=True, always=True)
    def format_datetime(cls, value):
        """Ensure datetime is always serialized as BRO required format"""
        if isinstance(value, datetime):
            return value.isoformat()
        return value


class Analysis(BaseModel):
    parameter: str | int
    unit: str
    analysisMeasurementValue: str | float
    limitSymbol: str | None = None
    reportingLimit: str | float | None = None
    qualityControlStatus: str


class AnalysisProcess(BaseModel):
    date: str | date
    analyticalTechnique: str
    valuationMethod: str
    analyses: list[Analysis]

    @validator("date", pre=True, always=True)
    def format_date(cls, value):
        """Ensure date is always serialized as a string, in BRO required format"""
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        return value


class LaboratoryAnalysis(BaseModel):
    responsibleLaboratoryKvk: str | None = None
    analysisProcesses: list[AnalysisProcess] = []


class GAR(BaseModel):
    objectIdAccountableParty: str
    qualityControlMethod: str
    groundwaterMonitoringNets: list[str] | None = None
    gmwBroId: str
    tubeNumber: str | int
    fieldResearch: FieldResearch
    laboratoryAnalyses: list[LaboratoryAnalysis] | None = None


# GLD
class GLDStartregistration(BaseModel):
    objectIdAccountableParty: str | None = None
    groundwaterMonitoringNets: list[str] | None = None
    gmwBroId: str
    tubeNumber: str | int


class TimeValuePair(BaseModel):
    time: str | datetime
    value: float | str
    statusQualityControl: str
    censorReason: str | None = None
    censoringLimitvalue: str | float | None = None

    @validator("time", pre=True, always=True)
    def format_datetime(cls, value):
        """Ensure datetime is always serialized as BRO required format"""
        if isinstance(value, datetime):
            return value.isoformat()
        return value


class GLDAddition(BaseModel):
    date: str
    observationId: str | None = None
    observationProcessId: str | None = None
    measurementTimeseriesId: str | None = None
    validationStatus: str | None = None
    investigatorKvk: str
    observationType: str
    evaluationProcedure: str
    measurementInstrumentType: str
    processReference: str
    airPressureCompensationType: str | None = None
    beginPosition: str
    endPosition: str
    resultTime: str
    timeValuePairs: list[TimeValuePair]

    @validator("observationId", pre=True, always=True)
    def format_observationId(cls, value):
        """Ensure the observationId is always filled with an uuid"""
        if not value:
            return f"_{uuid.uuid4()}"
        return value

    @validator("observationProcessId", pre=True, always=True)
    def format_observationProcessId(cls, value):
        """Ensure the observationProcessId is always filled with an uuid"""
        if not value:
            return f"_{uuid.uuid4()}"
        return value

    @validator("measurementTimeseriesId", pre=True, always=True)
    def format_measurementTimeseriesId(cls, value):
        """Ensure the measurementTimeseriesId is always filled with an uuid"""
        if not value:
            return f"_{uuid.uuid4()}"
        return value

    @validator("validationStatus", pre=True, always=True)
    def format_validationStatus(cls, value):
        """Ensure the measurementTimeseriesId is always filled with an uuid"""
        if cls.observationType == "reguliereMeting" and not value:
            return "onbekend"
        elif cls.observationType == "controlemeting":
            return None
        return value


# FRD
class FRDStartRegistration(BaseModel):
    objectIdAccountableParty: str | None = None
    groundwaterMonitoringNets: list[str] | None = None
    gmwBroId: str
    tubeNumber: str | int


class MeasurementConfiguration(BaseModel):
    measurementConfigurationID: str
    measurementE1CableNumber: str | int
    measurementE1ElectrodeNumber: str | int
    measurementE2CableNumber: str | int
    measurementE2ElectrodeNumber: str | int
    currentE1CableNumber: str | int
    currentE1ElectrodeNumber: str | int
    currentE2CableNumber: str | int
    currentE2ElectrodeNumber: str | int


class FRDGemMeasurementConfiguration(BaseModel):
    measurementConfigurations: list[MeasurementConfiguration]


class FRDEmmInstrumentConfiguration(BaseModel):
    instrumentConfigurationID: str
    relativePositionTransmitterCoil: str | int
    relativePositionPrimaryReceiverCoil: str | int
    secondaryReceiverCoilAvailable: str
    relativePositionSecondaryReceiverCoil: str | int | None = None
    coilFrequencyKnown: str
    coilFrequency: str | int | None = None
    instrumentLength: str | int


class FRDEmmMeasurement(BaseModel):
    measurementDate: date | str
    measurementOperatorKvk: str
    determinationProcedure: str
    measurementEvaluationProcedure: str
    measurementSeriesCount: str | int
    measurementSeriesValues: str
    relatedInstrumentConfigurationId: str
    calculationOperatorKvk: str
    calculationEvaluationProcedure: str
    calculationCount: str | int
    calculationValues: str


class GemMeasurement(BaseModel):
    value: str | int
    unit: str
    configuration: str


class RelatedCalculatedApparentFormationResistance(BaseModel):
    calculationOperatorKvk: str
    evaluationProcedure: str
    elementCount: str | int
    values: str


class FRDGemMeasurement(BaseModel):
    measurementDate: str | date
    measurementOperatorKvk: str
    determinationProcedure: str
    evaluationProcedure: str
    measurements: list[GemMeasurement]
    relatedCalculatedApparentFormationResistance: RelatedCalculatedApparentFormationResistance | None = None
