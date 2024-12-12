from api.bro_upload.upload_datamodels import (
    GAR,
    FRDEmmInstrumentConfiguration,
    FRDEmmMeasurement,
    FRDGemMeasurement,
    FRDGemMeasurementConfiguration,
    FRDStartRegistration,
    GLDAddition,
    GLDStartregistration,
    GMNClosure,
    GMNMeasuringPoint,
    GMNMeasuringPointEndDate,
    GMNStartregistration,
    GMNTubeReference,
    GMWConstruction,
    GMWElectrodeStatus,
    GMWGroundLevel,
    GMWGroundLevelMeasuring,
    GMWInsertion,
    GMWLengthening,
    GMWMaintainer,
    GMWOwner,
    GMWPositions,
    GMWPositionsMeasuring,
    GMWRemoval,
    GMWShift,
    GMWShortening,
    GMWTubeStatus,
    GMWWellHeadProtector,
)

STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("PROCESSING", "Processing"),
    ("COMPLETED", "Completed"),
    ("FAILED", "Failed"),
    ("UNFINISHED", "Unfinished"),
]

BRO_DOMAIN_CHOICES = [
    ("GMN", "GMN"),
    ("GMW", "GMW"),
    ("GLD", "GLD"),
    ("FRD", "FRD"),
    ("GAR", "GAR"),
]

BULK_UPLOAD_TYPES = [
    ("GAR", "GAR"),
    ("GLD", "GLD"),
]

# NOTE: Add new registration types to the registration_type_datamodel_mapping below
REGISTRATION_TYPE_OPTIONS = [
    ("GMN_StartRegistration", "GMN_StartRegistration"),
    ("GMN_MeasuringPoint", "GMN_MeasuringPoint"),
    ("GMN_MeasuringPointEndDate", "GMN_MeasuringPointEndDate"),
    ("GMN_TubeReference", "GMN_TubeReference"),
    ("GMN_Closure", "GMN_Closure"),
    ("GMW_Construction", "GMW_Construction"),
    ("GMW_ElectrodeStatus", "GMW_ElectrodeStatus"),
    ("GMW_GroundLevel", "GMW_GroundLevel"),
    ("GMW_GroundLevelMeasuring", "GMW_GroundLevelMeasuring"),
    ("GMW_Insertion", "GMW_Insertion"),
    ("GMW_Lengthening", "GMW_Lengthening"),
    ("GMW_Shortening", "GMW_Shortening"),
    ("GMW_Positions", "GMW_Positions"),
    ("GMW_PositionsMeasuring", "GMW_PositionsMeasuring"),
    ("GMW_Shift", "GMW_Shift"),
    ("GMW_Maintainer", "GMW_Maintainer"),
    ("GMW_Owner", "GMW_Owner"),
    ("GMW_Removal", "GMW_Removal"),
    ("GMW_TubeStatus", "GMW_TubeStatus"),
    ("GMW_WellHeadProtector", "GMW_WellHeadProtector"),
    ("GAR", "GAR"),
    ("GLD_StartRegistration", "GLD_StartRegistration"),
    ("GLD_Addition", "GLD_Addition"),
    ("GLD_Closure", "GLD_Closure"),
    ("FRD_StartRegistration", "FRD_StartRegistration"),
    ("FRD_GEM_MeasurementConfiguration", "FRD_GEM_MeasurementConfiguration"),
    ("FRD_GEM_Measurement", "GLD_CloFRD_GEM_Measurementsure"),
    ("FRD_EMM_InstrumentConfiguration", "FRD_EMM_InstrumentConfiguration"),
    ("FRD_EMM_Measurement", "FRD_EMM_Measurement"),
    ("FRD_Closure", "FRD_Closure"),
]


registration_type_datamodel_mapping = {
    "GMN_StartRegistration": GMNStartregistration,
    "GMN_MeasuringPoint": GMNMeasuringPoint,
    "GMN_MeasuringPointEndDate": GMNMeasuringPointEndDate,
    "GMN_TubeReference": GMNTubeReference,
    "GMN_Closure": GMNClosure,
    "GMW_Construction": GMWConstruction,
    "GMW_ElectrodeStatus": GMWElectrodeStatus,
    "GMW_GroundLevel": GMWGroundLevel,
    "GMW_GroundLevelMeasuring": GMWGroundLevelMeasuring,
    "GMW_Insertion": GMWInsertion,
    "GMW_Lengthening": GMWLengthening,
    "GMW_Shortening": GMWShortening,
    "GMW_Positions": GMWPositions,
    "GMW_PositionsMeasuring": GMWPositionsMeasuring,
    "GMW_Shift": GMWShift,
    "GMW_Maintainer": GMWMaintainer,
    "GMW_Owner": GMWOwner,
    "GMW_Removal": GMWRemoval,
    "GMW_WellHeadProtector": GMWWellHeadProtector,
    "GMW_TubeStatus": GMWTubeStatus,
    "GAR": GAR,
    "GLD_StartRegistration": GLDStartregistration,
    "GLD_Addition": GLDAddition,
    "GLD_Closure": None,
    "FRD_StartRegistration": FRDStartRegistration,
    "FRD_GEM_MeasurementConfiguration": FRDGemMeasurementConfiguration,
    "FRD_GEM_Measurement": FRDGemMeasurement,
    "FRD_EMM_InstrumentConfiguration": FRDEmmInstrumentConfiguration,
    "FRD_EMM_Measurement": FRDEmmMeasurement,
    "FRD_Closure": None,
}


REQUEST_TYPE_OPTIONS = [
    ("registration", "registration"),
    ("replace", "replace"),
    ("move", "move"),
    ("insert", "insert"),
    ("delete", "delete"),
]
