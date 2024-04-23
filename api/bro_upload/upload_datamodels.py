from pydantic import BaseModel


class Metadata(BaseModel):
    requestReference: str
    deliveryAccountableParty: str
    qualityRegime: str
    broId: str| None = None
    underPrivilege: str | None = None
    correctionReason: str | None = None

class MeasuringPoint(BaseModel):
    measuringPointCode: str
    broId: str
    tubeNumber: str

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
    tubeNumber: str

class GMNMeasuringPointEndDate(BaseModel):
    eventDate: str
    measuringPointCode: str
    broId: str
    tubeNumber: str

class GMNTubeReference(BaseModel):
    eventDate: str
    measuringPointCode: str

class GMNClosure(BaseModel):
    endDateMonitoring: str

class Electrode(BaseModel):
    electrodeNumber: str
    electrodePackingMaterial: str
    electrodeStatus: str
    electrodeStatus: str

class GeoOhmCable(BaseModel):
    cableNumber: str
    electrodes: list[Electrode]

class MonitoringTube(BaseModel):
    tubeNumber: str
    tubeType: str
    artesianWellCapPresent: str
    sedimentSumpPresent: str
    numberOfGeoOhmCables: str
    tubeTopDiameter: str
    variableDiameter: str
    tubeStatus: str
    tubeTopPosition: str
    tubeTopPositioningMethod: str
    tubePackingMaterial: str
    tubeMaterial: str
    glue: str
    screenLength: str
    sockMaterial: str
    plainTubePartLength: str
    sedimentSumpLength: str
    geoohmcables: list[GeoOhmCable] | None = None

class GMWConstruction(BaseModel):
    objectIdAccountableParty: str
    deliveryContext: str
    constructionStandard: str
    initialFunction: str
    numberOfMonitoringTubes: str
    groundLevelStable: str
    owner: str
    maintenanceResponsibleParty: str
    wellHeadProtector: str
    wellConstructionDate: str
    deliveredLocation: str
    horizontalPositioningMethod: str
    localVerticalReferencePoint: str
    offset: str
    verticalDatum: str
    groundLevelPosition: str
    groundLevelPositioningMethod: str
    monitoringTubes: list[MonitoringTube]






