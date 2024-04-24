from datetime import date, datetime

from pydantic import BaseModel


class Metadata(BaseModel):
    requestReference: str
    deliveryAccountableParty: str | None = None
    qualityRegime: str
    broId: str | None = None
    underPrivilege: str | None = None
    correctionReason: str | None = None


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


class FieldMeasurement(BaseModel):
    parameter: str | int
    unit: str
    fieldMeasurementValue: str | float
    qualityControlStatus: str


class FieldResearch(BaseModel):
    samplingDateTime: str | datetime
    chamberOfCommerceNumber: str
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


class Analysis(BaseModel):
    parameter: str | int
    unit: str
    analysisMeasurementValue: str | float
    limitSymbol: str | None = None
    reportingLimit: str | float = None
    qualityControlStatus: str


class AnalysisProcess(BaseModel):
    date: str | date
    analyticalTechnique: str
    valuationMethod: str
    analyses: list[Analysis]


class LaboratoryAnalysis(BaseModel):
    responsibleLaboratoryKvk: str | None = None
    analysisProcesses: list[AnalysisProcess]


class GAR(BaseModel):
    objectIdAccountableParty: str
    qualityControlMethod: str
    groundwaterMonitoringNets: list[str]
    gmwBroId: str
    tubeNumber: str | int
    fieldResearch: FieldResearch
    laboratoryAnalyses: list[LaboratoryAnalysis] | None = None
