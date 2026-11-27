"""Compare the GMN a client sends with the GMN in the BRO."""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Any

from .xml_reader import ParsedGMN, Tube

MEASURING_POINT = "GMN_MeasuringPoint"
TUBE_REFERENCE = "GMN_TubeReference"
END_DATE = "GMN_MeasuringPointEndDate"

ORDER = {END_DATE: 0, TUBE_REFERENCE: 1, MEASURING_POINT: 2}


@dataclass
class Action:
    registration_type: str
    measuring_point_code: str
    event_date: date
    old: Tube | None = None
    new: Tube | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "registration_type": self.registration_type,
            "measuring_point_code": self.measuring_point_code,
            "event_date": self.event_date.isoformat(),
        }
        for key in ("old", "new"):
            tube = getattr(self, key)
            if tube:
                result[key] = {"bro_id": tube.bro_id, "tube_number": tube.tube_number}
        return result

    def sourcedocument(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "eventDate": self.event_date.isoformat(),
            "measuringPointCode": self.measuring_point_code,
        }
        if self.new:
            document["broId"] = self.new.bro_id
            document["tubeNumber"] = self.new.tube_number
        return document


def _tube_label(tube: Tube) -> str:
    return f"{tube.bro_id} buis {tube.tube_number}"


def _date_errors(label: str, value: date, start: date | None, today: date) -> list[str]:
    if value > today:
        return [f"{label} {value} ligt in de toekomst."]
    if start and value < start:
        return [f"{label} {value} ligt vóór de begindatum van het meetnet ({start})."]
    return []


def _compare_point(
    gmn: ParsedGMN, point: dict[str, Any], default_event_date: date
) -> tuple[list[Action], list[str]]:
    """Return the action (or error) for one measuring point the client sent."""
    code = point["measuring_point_code"]
    known = gmn.measuring_points.get(code)

    if point["end_date"]:
        if known is None:
            return [], [f"{code}: dit meetpunt bestaat niet in {gmn.bro_id}."]
        if known.is_active:
            return [Action(END_DATE, code, point["end_date"])], []
        return [], []

    new = Tube(point["bro_id"], point["tube_number"])
    event_date = point["event_date"] or default_event_date

    if known is None:
        return [Action(MEASURING_POINT, code, event_date, new=new)], []
    if known.ended:
        ended_on = f"op {known.end_date}" if known.end_date else "(datum onbekend)"
        return [], [
            f"{code}: dit meetpunt is al beëindigd {ended_on}. "
            "Kies een nieuwe code voor een nieuw meetpunt."
        ]
    if known.tube != new:
        return [Action(TUBE_REFERENCE, code, event_date, old=known.tube, new=new)], []
    return [], []


def _shared_tube_errors(tube_users: dict[Tube, set[str]]) -> list[str]:
    return [
        f"{_tube_label(tube)} staat bij meer dan één meetpunt: "
        f"{', '.join(sorted(codes))}."
        for tube, codes in tube_users.items()
        if len(codes) > 1
    ]


def _moving_tube_errors(
    gmn: ParsedGMN, actions: list[Action], tube_users: dict[Tube, set[str]]
) -> list[str]:
    """A tube that another point still uses in the BRO.

    Whether the BRO accepts it depends on the order of delivery, so the client
    has to split it into two requests.
    """
    current_users = {
        point.tube: code
        for code, point in gmn.active_measuring_points.items()
        if point.tube
    }
    errors = []
    for action in actions:
        if action.new is None or len(tube_users[action.new]) > 1:
            continue
        holder = current_users.get(action.new)
        if holder and holder != action.measuring_point_code:
            target = action.measuring_point_code
            errors.append(
                f"{_tube_label(action.new)} gaat van meetpunt {holder} naar {target}. "
                f"Doe dit in twee requests: eerst {holder} (andere buis of "
                f"beëindigen), en als die taak klaar is {target}."
            )
    return errors


def compare(
    gmn: ParsedGMN,
    measuring_points: list[dict[str, Any]],
    default_event_date: date,
    today: date,
) -> tuple[list[Action], list[str]]:
    """Return the actions that bring the BRO in line with ``measuring_points``.

    Any error means no actions at all.
    """
    if gmn.ended:
        closed_on = gmn.end_date_monitoring or "(datum onbekend)"
        return [], [
            f"{gmn.bro_id} is in de BRO al afgesloten op {closed_on}. "
            "Er kunnen geen meetpunten meer bij of af."
        ]

    start = (
        date.fromisoformat(gmn.start_date_monitoring)
        if gmn.start_date_monitoring
        else None
    )
    errors = _date_errors("event_date", default_event_date, start, today)

    counts = Counter(point["measuring_point_code"] for point in measuring_points)
    errors += [
        f"{code}: deze code staat meer dan één keer in de lijst."
        for code, count in counts.items()
        if count > 1
    ]

    actions = []
    # Tube -> codes of the points that use it after this request.
    tube_users: dict[Tube, set[str]] = defaultdict(set)
    for point in measuring_points:
        code = point["measuring_point_code"]
        own_date = point["end_date"] or point["event_date"]
        if own_date:
            errors += _date_errors(f"{code}: datum", own_date, start, today)
        if not point["end_date"]:
            tube_users[Tube(point["bro_id"], point["tube_number"])].add(code)

        point_actions, point_errors = _compare_point(gmn, point, default_event_date)
        actions += point_actions
        errors += point_errors

    errors += _shared_tube_errors(tube_users)
    errors += _moving_tube_errors(gmn, actions, tube_users)
    if not tube_users:
        errors.append(
            f"Na deze wijzigingen heeft {gmn.bro_id} geen actief meetpunt meer. "
            "Een meetnet moet minstens één meetpunt houden."
        )
    if errors:
        return [], errors

    actions += [
        Action(END_DATE, code, default_event_date)
        for code in gmn.active_measuring_points
        if code not in counts
    ]
    actions.sort(
        key=lambda action: (
            action.event_date,
            ORDER[action.registration_type],
            action.measuring_point_code,
        )
    )
    return actions, []
