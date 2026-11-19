"""Helpers for validating and splitting new GLD additions."""

from datetime import timedelta
from statistics import median
from xml.etree.ElementTree import (  # nosec B405: Element is only used for type hinting
    Element,
    ParseError,
)

from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import fromstring

from api.bro_upload.upload_datamodels import GLDAddition, TimeValuePair
from gmw.xml_reader.namespaces import ns_reg_gmw

from ..client import get_text
from ..exceptions import CorrectionValidationError
from .matching import parse_time

GLDCOMMON = "http://www.broservices.nl/xsd/gldcommon/1.0"
MINIMUM_MEASUREMENTS_FOR_INTERVAL_INFERENCE = 50
MAX_INFERRED_INTERVAL = timedelta(days=1)


def _text(element: Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None


def _parse_xml(xml: str, description: str) -> Element:
    try:
        return fromstring(xml)
    except (ParseError, DefusedXmlException) as exc:
        raise CorrectionValidationError(
            f"De BRO gaf geen leesbare XML terug voor {description}."
        ) from exc


def _validate_bro_id(value: str, prefix: str) -> None:
    if len(value) != 15 or not value.startswith(prefix) or not value[3:].isdigit():
        raise CorrectionValidationError(f"'{value}' is not a valid {prefix} BRO ID.")


def fetch_tube_geometry(gld_id: str) -> tuple[float, float]:
    """Fetch tube top and bottom positions through the GLD-to-GMW relation."""
    _validate_bro_id(gld_id, "GLD")
    gld_xml = get_text(f"/gm/gld/v1/objects/{gld_id}")
    gld_root = _parse_xml(gld_xml, f"GLD {gld_id}")

    tube_reference = gld_root.find(f".//{{{GLDCOMMON}}}GroundwaterMonitoringTube")
    if tube_reference is None:
        raise CorrectionValidationError(
            f"GLD {gld_id} bevat geen gekoppelde grondwatermonitoringbuis."
        )

    gmw_id = _text(tube_reference.find(f"{{{GLDCOMMON}}}broId"))
    linked_tube_number = _text(tube_reference.find(f"{{{GLDCOMMON}}}tubeNumber"))
    selected_tube_number = linked_tube_number
    if not gmw_id or not selected_tube_number:
        raise CorrectionValidationError(
            f"De gekoppelde buisgegevens ontbreken in GLD {gld_id}."
        )
    _validate_bro_id(gmw_id, "GMW")
    gmw_xml = get_text(f"/gm/gmw/v1/objects/{gmw_id}", params={"fullHistory": "nee"})
    gmw_root = _parse_xml(gmw_xml, f"GMW {gmw_id}")
    for tube in gmw_root.findall(".//monitoringTube", ns_reg_gmw):
        if _text(tube.find("tubeNumber", ns_reg_gmw)) != selected_tube_number:
            continue

        top_text = _text(tube.find("tubeTopPosition", ns_reg_gmw))
        bottom_text = _text(tube.find("screen/screenBottomPosition", ns_reg_gmw))
        try:
            top = float(top_text) if top_text is not None else None
            bottom = float(bottom_text) if bottom_text is not None else None
        except ValueError as exc:
            raise CorrectionValidationError(
                f"De geometrie van buis {selected_tube_number} in GMW {gmw_id} is ongeldig."
            ) from exc

        if top is None or bottom is None:
            raise CorrectionValidationError(
                f"De top- of bodempositie van buis {selected_tube_number} in "
                f"GMW {gmw_id} ontbreekt."
            )
        return top, bottom

    raise CorrectionValidationError(
        f"Buis {selected_tube_number} is niet gevonden in GMW {gmw_id}."
    )


def _inferred_gap_cutoff(measurements: list[TimeValuePair]) -> timedelta:
    if len(measurements) < MINIMUM_MEASUREMENTS_FOR_INTERVAL_INFERENCE:
        return timedelta(days=1)

    sorted_times = sorted(parse_time(item.time) for item in measurements)
    intervals = [
        (current - previous).total_seconds()
        for previous, current in zip(sorted_times, sorted_times[1:])
        if current > previous
    ]
    if not intervals:
        inferred_interval = timedelta(days=1)
    else:
        inferred_interval = timedelta(seconds=median(intervals))

    inferred_interval = min(inferred_interval, MAX_INFERRED_INTERVAL)
    return inferred_interval * 24


def split_measurements(
    addition: GLDAddition,
) -> list[list[TimeValuePair]]:
    """Split an addition into periods when adjacent measurements have large gaps."""
    measurements = sorted(
        addition.time_value_pairs, key=lambda item: parse_time(item.time)
    )
    if not measurements:
        raise CorrectionValidationError(
            "Een GLD_Addition kan niet zonder metingen worden aangeleverd."
        )

    cutoff = _inferred_gap_cutoff(measurements)
    segments: list[list[TimeValuePair]] = [[measurements[0]]]
    for measurement in measurements[1:]:
        previous = segments[-1][-1]
        if parse_time(measurement.time) - parse_time(previous.time) > cutoff:
            segments.append([])
        segments[-1].append(measurement)
    return segments


def segment_period(
    measurements: list[TimeValuePair],
) -> tuple[str, str, str]:
    """Return date-precision begin/end and the latest measurement time."""
    if not measurements:
        raise CorrectionValidationError(
            "Een observatiesegment kan niet zonder metingen worden aangeleverd."
        )

    sorted_measurements = sorted(measurements, key=lambda item: parse_time(item.time))
    first = parse_time(sorted_measurements[0].time)
    last = parse_time(sorted_measurements[-1].time)
    return (
        first.date().isoformat(),
        last.date().isoformat(),
        last.isoformat(timespec="seconds"),
    )


def build_segment_addition(
    addition: GLDAddition,
    measurements: list[TimeValuePair],
) -> GLDAddition:
    """Copy the source fields and regenerate IDs and period fields for a segment."""
    begin, end, result = segment_period(measurements)
    payload = addition.model_dump(mode="python", by_alias=False, exclude_unset=True)
    for identifier in (
        "observation_id",
        "observation_process_id",
        "measurement_timeseries_id",
    ):
        payload.pop(identifier, None)

    payload["time_value_pairs"] = [
        measurement.model_dump(mode="python", by_alias=False)
        for measurement in measurements
    ]
    payload["begin_position"] = begin
    payload["end_position"] = end
    payload["result_time"] = result
    return GLDAddition(**payload)
