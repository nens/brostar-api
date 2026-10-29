"""Reader for a GLD dispatchDataResponse from the public BRO uitgifteservice.

Only the parts that are needed to rebuild a GLD_Addition are parsed. Elements
are looked up by namespace URI, because the BRO uses the ``waterml`` prefix
while the BROSTAR templates use ``wml2``.
"""

from dataclasses import dataclass, field
from typing import Any

from defusedxml import ElementTree

from ..exceptions import CorrectionValidationError

BROCOM = "http://www.broservices.nl/xsd/brocommon/3.0"
GLDCOMMON = "http://www.broservices.nl/xsd/gldcommon/1.0"
GML = "http://www.opengis.net/gml/3.2"
OM = "http://www.opengis.net/om/2.0"
SWE = "http://www.opengis.net/swe/2.0"
WML = "http://www.opengis.net/waterml/2.0"
XLINK = "http://www.w3.org/1999/xlink"

CENSOR_REASONS = {
    "BelowDetectionRange": "kleinerDanLimietwaarde",
    "AboveDetectionRange": "groterDanLimietwaarde",
    "unknown": "onbekend",
}

PROCEDURE_PARAMETERS = {
    "evaluationProcedure": "evaluation_procedure",
    "measurementInstrumentType": "measurement_instrument_type",
    "airPressureCompensationType": "air_pressure_compensation_type",
}


@dataclass
class Measurement:
    """A single MeasurementTVP."""

    time: str
    value: float | None = None
    status_quality_control: str = "onbekend"
    censor_reason: str | None = None
    censoring_limitvalue: float | None = None

    def as_payload(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "value": self.value,
            "statusQualityControl": self.status_quality_control,
            "censorReason": self.censor_reason,
            "censoringLimitvalue": self.censoring_limitvalue,
        }

    def content(self) -> tuple[Any, ...]:
        """Everything except the time; used to detect actual changes."""
        return (
            self.value,
            self.status_quality_control,
            self.censor_reason,
            self.censoring_limitvalue,
        )


@dataclass
class ParsedObservation:
    observation_id: str
    observation_process_id: str | None = None
    measurement_timeseries_id: str | None = None
    observation_type: str | None = None
    validation_status: str | None = None
    begin_position: str | None = None
    end_position: str | None = None
    result_time: str | None = None
    date_stamp: str | None = None
    process_reference: str | None = None
    evaluation_procedure: str | None = None
    measurement_instrument_type: str | None = None
    air_pressure_compensation_type: str | None = None
    repeat_procedure: bool = False
    investigator_kvk: str | None = None
    measurements: list[Measurement] = field(default_factory=list)

    def procedure(self) -> dict[str, str | None]:
        return {
            "process_reference": self.process_reference,
            "evaluation_procedure": self.evaluation_procedure,
            "measurement_instrument_type": self.measurement_instrument_type,
            "air_pressure_compensation_type": self.air_pressure_compensation_type,
            "validation_status": self.validation_status,
            "observation_type": self.observation_type,
        }


@dataclass
class ParsedGLD:
    bro_id: str | None = None
    quality_regime: str | None = None
    delivery_accountable_party: str | None = None
    observations: list[ParsedObservation] = field(default_factory=list)

    def get_observation(self, observation_id: str) -> ParsedObservation | None:
        for observation in self.observations:
            if observation.observation_id == observation_id:
                return observation
        return None


def _text(element: Any) -> str | None:
    if element is None or element.text is None:
        return None
    text = element.text.strip()
    return text or None


def _href_suffix(element: Any) -> str | None:
    """Return the part after the last ':' or '/' of an xlink:href."""
    if element is None:
        return None
    href = element.get(f"{{{XLINK}}}href")
    if not href:
        return None
    return href.rsplit(":", 1)[-1].rsplit("/", 1)[-1]


def _float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _named_values(parent: Any) -> dict[str, str | None]:
    """Collect om:NamedValue pairs keyed on the last part of the om:name href."""
    values: dict[str, str | None] = {}
    for named_value in parent.iter(f"{{{OM}}}NamedValue"):
        name = _href_suffix(named_value.find(f"{{{OM}}}name"))
        if name:
            values[name] = _text(named_value.find(f"{{{OM}}}value"))
    return values


def _parse_measurement(tvp: Any) -> Measurement:
    time = _text(tvp.find(f"{{{WML}}}time")) or ""
    value_element = tvp.find(f"{{{WML}}}value")
    measurement = Measurement(time=time, value=_float(_text(value_element)))

    metadata = tvp.find(f"{{{WML}}}metadata")
    if metadata is None:
        return measurement

    for qualifier in metadata.iter(f"{{{WML}}}qualifier"):
        category = qualifier.find(f"{{{SWE}}}Category")
        if category is not None:
            measurement.status_quality_control = (
                _text(category.find(f"{{{SWE}}}value")) or "onbekend"
            )
            continue

        quantity = qualifier.find(f"{{{SWE}}}Quantity")
        if quantity is not None:
            measurement.censoring_limitvalue = _float(
                _text(quantity.find(f"{{{SWE}}}value"))
            )

    censored_reason = _href_suffix(metadata.find(f".//{{{WML}}}censoredReason"))
    if censored_reason:
        measurement.censor_reason = CENSOR_REASONS.get(censored_reason, "onbekend")

    return measurement


def _parse_procedure(observation: ParsedObservation, procedure: Any) -> None:
    href = procedure.get(f"{{{XLINK}}}href")
    process = procedure.find(f"{{{WML}}}ObservationProcess")

    if process is None:
        # A referenced procedure: the process is defined in another observation.
        observation.repeat_procedure = True
        observation.observation_process_id = (href or "").lstrip("#") or None
        return

    observation.observation_process_id = process.get(f"{{{GML}}}id")
    observation.process_reference = _href_suffix(
        process.find(f"{{{WML}}}processReference")
    )

    parameters = _named_values(process)
    for bro_name, attribute in PROCEDURE_PARAMETERS.items():
        setattr(observation, attribute, parameters.get(bro_name))


def _parse_observation(element: Any) -> ParsedObservation:
    observation = ParsedObservation(
        observation_id=element.get(f"{{{GML}}}id") or "",
    )

    metadata = element.find(f"{{{OM}}}metadata")
    if metadata is not None:
        observation.validation_status = _href_suffix(
            metadata.find(f".//{{{WML}}}status")
        )
        observation.date_stamp = _text(metadata.find(f".//{{{GML}}}Date")) or _text(
            metadata.find(".//{http://www.isotc211.org/2005/gco}Date")
        )
        named_values = _named_values(metadata)
        observation.observation_type = named_values.get("observationType")
        observation.investigator_kvk = _text(
            metadata.find(f".//{{{GLDCOMMON}}}chamberOfCommerceNumber")
        )

    time_period = element.find(f"{{{OM}}}phenomenonTime/{{{GML}}}TimePeriod")
    if time_period is not None:
        observation.begin_position = _text(time_period.find(f"{{{GML}}}beginPosition"))
        observation.end_position = _text(time_period.find(f"{{{GML}}}endPosition"))

    observation.result_time = _text(
        element.find(f"{{{OM}}}resultTime/{{{GML}}}TimeInstant/{{{GML}}}timePosition")
    )

    procedure = element.find(f"{{{OM}}}procedure")
    if procedure is not None:
        _parse_procedure(observation, procedure)

    timeseries = element.find(f"{{{OM}}}result/{{{WML}}}MeasurementTimeseries")
    if timeseries is not None:
        observation.measurement_timeseries_id = timeseries.get(f"{{{GML}}}id")
        observation.measurements = [
            _parse_measurement(tvp)
            for tvp in timeseries.iter(f"{{{WML}}}MeasurementTVP")
        ]

    return observation


def parse_gld_response(xml_string: str) -> ParsedGLD:
    """Parse a dispatchDataResponse into a ParsedGLD."""
    try:
        root = ElementTree.fromstring(xml_string.encode("utf-8"))
    except ElementTree.ParseError as exc:
        raise CorrectionValidationError(
            f"De BRO gaf geen leesbare XML terug: {exc}"
        ) from exc

    parsed = ParsedGLD(
        bro_id=_text(root.find(f".//{{{BROCOM}}}broId")),
        quality_regime=_text(root.find(f".//{{{BROCOM}}}qualityRegime")),
        delivery_accountable_party=_text(
            root.find(f".//{{{BROCOM}}}deliveryAccountableParty")
        ),
    )

    parsed.observations = [
        _parse_observation(element) for element in root.iter(f"{{{OM}}}OM_Observation")
    ]

    return parsed
