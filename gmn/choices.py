GMN_EVENT_TYPES = (
    ("GMN_MeasuringPoint", "GMN_MeasuringPoint"),
    ("GMN_TubeReference", "GMN_TubeReference"),
    ("GMN_MeasuringPointEndDate", "GMN_MeasuringPointEndDate"),
    ("GMN_StartRegistration", "GMN_StartRegistration"),
)

GMN_EVENT_MAPPING = {
    "meetpuntToevoegen": "GMN_MeasuringPoint",
    "monitoringbuisVervangen": "GMN_TubeReference",
    "meetpuntBeeindigen": "GMN_MeasuringPointEndDate",
}
