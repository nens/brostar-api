from api.bro_upload.upload_datamodels import (
    GAR,
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

# NOTE: Add new registration types to the registration_type_datamodel_mapping below
REGISTRATION_TYPE_OPTIONS = [
    ("GMN_StartRegistration", "GMN_StartRegistration"),
    ("GMN_MeasuringPoint", "GMN_MeasuringPoint"),
    ("GMN_MeasuringPointEndDate", "GMN_MeasuringPointEndDate"),
    ("GMN_TubeReference", "GMN_TubeReference"),
    ("GMN_Closure", "GMN_Closure"),
    ("GMW_Construction", "GMW_Construction"),
    ("GAR", "GAR"),
]


registration_type_datamodel_mapping = {
    "GMN_StartRegistration": GMNStartregistration,
    "GMN_MeasuringPoint": GMNMeasuringPoint,
    "GMN_MeasuringPointEndDate": GMNMeasuringPointEndDate,
    "GMN_TubeReference": GMNTubeReference,
    "GMN_Closure": GMNClosure,
    "GMW_Construction": GMWConstruction,
    "GAR": GAR,
}


REQUEST_TYPE_OPTIONS = [
    ("registration", "registration"),
    ("replace", "replace"),
    ("move", "move"),
    ("insert", "insert"),
    ("delete", "delete"),
]
