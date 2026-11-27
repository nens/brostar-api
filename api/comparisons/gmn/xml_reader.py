"""Read the current state of a GMN from a BRO dispatch response."""

import xml.etree.ElementTree as ET  # nosec B405
from dataclasses import dataclass

from defusedxml.ElementTree import fromstring

from api.bro_import.bro_xml_reader import _date_text
from api.bro_import.namespaces import ns_reg_gmn_tot as NS


@dataclass(frozen=True)
class Tube:
    bro_id: str
    tube_number: int


@dataclass
class ParsedMeasuringPoint:
    code: str
    start_date: str | None
    # ``ended`` is separate from ``end_date``: the date may be unknown (voidReason).
    ended: bool
    end_date: str | None
    tube: Tube | None

    @property
    def is_active(self) -> bool:
        return not self.ended


@dataclass
class ParsedGMN:
    bro_id: str
    delivery_accountable_party: str | None
    quality_regime: str | None
    start_date_monitoring: str | None
    ended: bool
    end_date_monitoring: str | None
    measuring_points: dict[str, ParsedMeasuringPoint]

    @property
    def active_measuring_points(self) -> dict[str, ParsedMeasuringPoint]:
        return {
            code: point
            for code, point in self.measuring_points.items()
            if point.is_active
        }


def _text(element: ET.Element, path: str) -> str | None:
    found = element.find(path, NS)
    return found.text if found is not None else None


def _current_tube(measuring_point: ET.Element) -> Tube | None:
    for tube in measuring_point.findall("monitoringTube/GroundwaterMonitoringTube", NS):
        if tube.find("endDate", NS) is None:
            return Tube(
                bro_id=_text(tube, "broId") or "",
                tube_number=int(_text(tube, "tubeNumber") or 0),
            )
    return None


def _parse_measuring_point(measuring_point: ET.Element) -> ParsedMeasuringPoint:
    # Direct children only: a tube has its own startDate and endDate.
    end_date = measuring_point.find("endDate", NS)
    return ParsedMeasuringPoint(
        code=_text(measuring_point, "measuringPointCode") or "",
        start_date=_date_text(measuring_point.find("startDate", NS), NS),
        ended=end_date is not None,
        end_date=_date_text(end_date, NS),
        tube=_current_tube(measuring_point),
    )


def parse_gmn_response(xml_string: str) -> ParsedGMN:
    root = fromstring(xml_string.encode("utf-8"))
    document = root.find("dispatchDocument/*", NS)
    if document is None:
        raise ValueError("Het BRO-antwoord bevat geen GMN.")

    history = document.find("monitoringNetHistory", NS)
    end_date_monitoring = (
        history.find("endDateMonitoring", NS) if history is not None else None
    )

    points = [
        _parse_measuring_point(point)
        for point in document.findall("measuringPoint/MeasuringPoint", NS)
    ]

    return ParsedGMN(
        bro_id=_text(document, "brocom:broId") or "",
        delivery_accountable_party=_text(document, "brocom:deliveryAccountableParty"),
        quality_regime=_text(document, "brocom:qualityRegime"),
        start_date_monitoring=_date_text(
            history.find("startDateMonitoring", NS) if history is not None else None,
            NS,
        ),
        ended=end_date_monitoring is not None,
        end_date_monitoring=_date_text(end_date_monitoring, NS),
        measuring_points={point.code: point for point in points},
    )
