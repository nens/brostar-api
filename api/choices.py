from api.bro_upload.upload_datamodels import (
    GAR,
    FRDEmmMeasurement,
    FRDEmmMeasurementConfiguration,
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
]

# NOTE: Add new registration types to the registration_type_datamodel_mapping below
REGISTRATION_TYPE_OPTIONS = [
    ("GMN_StartRegistration", "GMN_StartRegistration"),
    ("GMN_MeasuringPoint", "GMN_MeasuringPoint"),
    ("GMN_MeasuringPointEndDate", "GMN_MeasuringPointEndDate"),
    ("GMN_TubeReference", "GMN_TubeReference"),
    ("GMN_Closure", "GMN_Closure"),
    ("GMW_Construction", "GMW_Construction"),
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
    "GAR": GAR,
    "GLD_StartRegistration": GLDStartregistration,
    "GLD_Addition": GLDAddition,
    "GLD_Closure": None,
    "FRD_StartRegistration": FRDStartRegistration,
    "FRD_GEM_MeasurementConfiguration": FRDGemMeasurementConfiguration,
    "FRD_GEM_Measurement": FRDGemMeasurement,
    "FRD_EMM_InstrumentConfiguration": FRDEmmMeasurementConfiguration,
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
