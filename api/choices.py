STATUS_CHOICES = [
    ("PENDING", "Pending"),
    ("PROCESSING", "Processing"),
    ("COMPLETED", "Completed"),
    ("FAILED", "Failed"),
]

BRO_DOMAIN_CHOICES = [
    ("GMN", "GMN"),
    ("GMW", "GMW"),
    ("GLD", "GLD"),
    ("FRD", "FRD"),
]

REGISTRATION_TYPE_OPTIONS = [
    ("GMN_StartRegistration", "GMN_StartRegistration"),
    ("GMN_MeasuringPoint", "GMN_MeasuringPoint"),
    ("GMN_MeasuringPointEndDate", "GMN_MeasuringPointEndDate"),
    ("GMN_TubeReference", "GMN_TubeReference"),
    ("GMN_Closure", "GMN_Closure"),
    ("GMW", "GWM"),
]

REQUEST_TYPE_OPTIONS = [
    ("registration", "registration"),
    ("replace", "replace"),
    ("move", "move"),
    ("insert", "insert"),
    ("delete", "delete"),
]
