from typing import Literal

QualityRegimeOptions = Literal["IMBRO", "IMBRO/A"]
CorrectionReasonOptions = Literal[
    "eigenCorrectie", "bronhouder", "kwaliteitsregime", "inOnderzoek"
]
BroDomainOptions = Literal["GMW", "GMN", "GAR", "GLD", "FRD"]
RequestTypeOptions = Literal["registration", "replace", "insert", "move", "delete"]
RegistrationTypeOptions = Literal[
    "GMW_Construction",
    "GMW_ElectrodeStatus",
    "GMW_GroundLevel",
    "GMW_GroundLevelMeasuring",
    "GMW_Insertion",
    "GMW_Lengthening",
    "GMW_Maintainer",
    "GMW_Owner",
    "GMW_Positions",
    "GMW_PositionsMeasuring",
    "GMW_Removal",
    "GMW_Shift",
    "GMW_Shortening",
    "GMW_TubeStatus",
    "GMW_WellHeadProtector",
    "GMN_Startregistration",
    "GMN_MeasuringPoint",
    "GMN_MeasuringPointEndDate",
    "GMN_TubeReference",
    "GMN_Closure",
    "GAR",
    "GLD_StartRegistration",
    "GLD_Addition",
    "GLD_Closure",
]
