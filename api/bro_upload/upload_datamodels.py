from pydantic import BaseModel


class Metadata(BaseModel):
    requestReference: str
    deliveryAccountableParty: str
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
