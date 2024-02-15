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
]

REQUEST_TYPE_OPTIONS = [
    ("register", "register"),
    ("replace", "replace"),
    ("move", "move"),
    ("insert", "insert"),
    ("delete", "delete"),
]
