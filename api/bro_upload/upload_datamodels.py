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
    electrodePosition: str


class GeoOhmCable(BaseModel):
    cableNumber: str | int
    electrodes: list[Electrode]


class MonitoringTube(BaseModel):
    tubeNumber: str | int
    tubeType: str
    artesianWellCapPresent: str
    sedimentSumpPresent: str
    numberOfGeoOhmCables: str | int
    tubeTopDiameter: str | float
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
    sedimentSumpLength: str | float
    geoohmcables: list[GeoOhmCable] | None = None


class GMWConstruction(BaseModel):
    objectIdAccountableParty: str
    deliveryContext: str
    constructionStandard: str
    initialFunction: str
    numberOfMonitoringTubes: str | int
    groundLevelStable: str
    owner: str
    maintenanceResponsibleParty: str
    wellHeadProtector: str
    wellConstructionDate: str
    deliveredLocation: str
    horizontalPositioningMethod: str
    localVerticalReferencePoint: str
    offset: str | float
    verticalDatum: str
    groundLevelPosition: str | float
    groundLevelPositioningMethod: str
    monitoringTubes: list[MonitoringTube]


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


class GLDStartregistration(BaseModel):
    objectIdAccountableParty: str | None = None
    groundwaterMonitoringNets: list[str] | None = None
    gmwBroId: str
    tubeNumber: str | int


class TimeValuePair(BaseModel):
    time: str | datetime
    value: float | str
    statusQualityControl: str

    @validator("samplingDateTime", pre=True, always=True)
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
