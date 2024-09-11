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
    eventDate: str
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
    numberOfGeoOhmCables: str | int
    tubeTopDiameter: str | float | None = None
    variableDiameter: str | float
    tubeStatus: str
    tubeTopPosition: str | float
    tubeTopPositioningMethod: str
    tubePackingMaterial: str
    tubeMaterial: str
    glue: str
    screenLength: str | float
    sockMaterial: str
    plainTubePartLength: str | float
    sedimentSumpLength: str | float | None = None
    geoohmcables: list[GeoOhmCable] | None = None


class GMWConstruction(BaseModel):
    objectIdAccountableParty: str
    deliveryContext: str
    constructionStandard: str
    initialFunction: str
    numberOfMonitoringTubes: str | int
    groundLevelStable: str
    wellStability: str | None = None
    owner: str
    maintenanceResponsibleParty: str
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
    tubeStatus: str
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

    @validator("time", pre=True, always=True)
    def format_datetime(cls, value):
        """Ensure datetime is always serialized as BRO required format"""
        if isinstance(value, datetime):
            return value.isoformat()
        return value


class GLDAddition(BaseModel):
    principalInvestigator: str
    date: str
    investigatorKvk: str
    observationType: str
    beginPosition: str
    endPosition: str
    resultTime: str
    evaluationProcedure: str
    measurementInstrumentType: str
    timeValuePairs: list[TimeValuePair]


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
