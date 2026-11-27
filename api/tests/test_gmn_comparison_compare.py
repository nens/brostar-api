from datetime import date
from pathlib import Path

from api.comparisons.gmn.compare import Action, compare
from api.comparisons.gmn.xml_reader import Tube, parse_gmn_response

XML_DIR = Path(__file__).parent / "xml_strings"

# A: GMW...001 tube 1, B: GMW...003 tube 2 (replaced earlier), C and D ended.
GMN = parse_gmn_response(
    (XML_DIR / "gmn_comparison_ended_point.xml").read_text(encoding="utf-8")
)
TODAY = date(2026, 11, 27)


def point(code, bro_id=None, tube_number=None, event_date=None, end_date=None):
    return {
        "measuring_point_code": code,
        "bro_id": bro_id,
        "tube_number": tube_number,
        "event_date": event_date,
        "end_date": end_date,
    }


A = point("A", "GMW000000000001", 1)
B = point("B", "GMW000000000003", 2)


def run(*points, gmn=GMN, default=TODAY):
    return compare(gmn, list(points), default_event_date=default, today=TODAY)


def test_unchanged_network_gives_no_actions():
    assert run(A, B) == ([], [])


def test_new_code_gives_measuring_point_on_default_date():
    actions, errors = run(A, B, point("E", "GMW000000000006", 1))

    assert errors == []
    assert actions == [
        Action(
            registration_type="GMN_MeasuringPoint",
            measuring_point_code="E",
            event_date=TODAY,
            new=Tube("GMW000000000006", 1),
        )
    ]


def test_other_tube_gives_tube_reference_on_own_date():
    moved = point("B", "GMW000000000009", 1, event_date=date(2026, 10, 1))

    actions, errors = run(A, moved)

    assert errors == []
    assert actions == [
        Action(
            registration_type="GMN_TubeReference",
            measuring_point_code="B",
            event_date=date(2026, 10, 1),
            old=Tube("GMW000000000003", 2),
            new=Tube("GMW000000000009", 1),
        )
    ]


def test_missing_active_point_ends_on_default_date():
    actions, errors = run(A, default=date(2026, 11, 1))

    assert errors == []
    assert actions == [
        Action(
            registration_type="GMN_MeasuringPointEndDate",
            measuring_point_code="B",
            event_date=date(2026, 11, 1),
        )
    ]


def test_ended_code_sent_as_active_is_refused():
    actions, errors = run(A, B, point("C", "GMW000000000004", 1))

    assert actions == []
    assert errors == [
        "C: dit meetpunt is al beëindigd op 2023-05-01. "
        "Kies een nieuwe code voor een nieuw meetpunt."
    ]


def test_end_date_for_ended_code_does_nothing():
    assert run(A, B, point("C", end_date=date(2023, 5, 1))) == ([], [])


def test_end_date_for_unknown_code_is_refused():
    actions, errors = run(A, B, point("X", end_date=date(2026, 11, 20)))

    assert actions == []
    assert errors == ["X: dit meetpunt bestaat niet in GMN000000000999."]


def test_duplicate_code_is_refused():
    actions, errors = run(A, B, A)

    assert actions == []
    assert errors == ["A: deze code staat meer dan één keer in de lijst."]


def test_same_tube_at_two_points_is_refused():
    actions, errors = run(A, B, point("E", "GMW000000000001", 1))

    assert actions == []
    assert errors == ["GMW000000000001 buis 1 staat bij meer dan één meetpunt: A, E."]


def test_tube_moving_to_other_point_is_refused():
    # B is left out (ends) and its tube goes to the new point E.
    actions, errors = run(A, point("E", "GMW000000000003", 2))

    assert actions == []
    assert errors == [
        "GMW000000000003 buis 2 gaat van meetpunt B naar E. Doe dit in twee "
        "requests: eerst B (andere buis of beëindigen), en als die taak klaar is E."
    ]


def test_points_swapping_tubes_is_refused():
    actions, errors = run(
        point("A", "GMW000000000003", 2), point("B", "GMW000000000001", 1)
    )

    assert actions == []
    assert len(errors) == 2


def test_actions_are_sorted_by_date():
    actions, errors = run(
        point("A", "GMW000000000009", 1, event_date=date(2026, 10, 1)),
        point("E", "GMW000000000006", 1, event_date=date(2026, 9, 1)),
        default=date(2026, 11, 1),
    )

    assert errors == []
    assert [(a.measuring_point_code, a.event_date) for a in actions] == [
        ("E", date(2026, 9, 1)),
        ("A", date(2026, 10, 1)),
        ("B", date(2026, 11, 1)),
    ]


def test_action_as_response():
    action = Action(
        registration_type="GMN_TubeReference",
        measuring_point_code="B",
        event_date=date(2026, 10, 1),
        old=Tube("GMW000000000003", 2),
        new=Tube("GMW000000000009", 1),
    )

    assert action.to_dict() == {
        "registration_type": "GMN_TubeReference",
        "measuring_point_code": "B",
        "event_date": "2026-10-01",
        "old": {"bro_id": "GMW000000000003", "tube_number": 2},
        "new": {"bro_id": "GMW000000000009", "tube_number": 1},
    }
    assert Action("GMN_MeasuringPointEndDate", "C", date(2026, 11, 20)).to_dict() == {
        "registration_type": "GMN_MeasuringPointEndDate",
        "measuring_point_code": "C",
        "event_date": "2026-11-20",
    }


def test_action_as_sourcedocument():
    new_point = Action(
        "GMN_MeasuringPoint", "E", date(2026, 9, 1), new=Tube("GMW000000000006", 1)
    )
    end = Action("GMN_MeasuringPointEndDate", "C", date(2026, 11, 20))

    assert new_point.sourcedocument() == {
        "eventDate": "2026-09-01",
        "measuringPointCode": "E",
        "broId": "GMW000000000006",
        "tubeNumber": 1,
    }
    assert end.sourcedocument() == {
        "eventDate": "2026-11-20",
        "measuringPointCode": "C",
    }


def test_no_active_point_left_is_refused():
    ended = date(2026, 11, 20)
    expected = [
        "Na deze wijzigingen heeft GMN000000000999 geen actief meetpunt meer. "
        "Een meetnet moet minstens één meetpunt houden."
    ]

    assert run() == ([], expected)
    assert run(point("A", end_date=ended), point("B", end_date=ended)) == (
        [],
        expected,
    )


def test_date_in_future_is_refused():
    actions, errors = run(A, B, point("E", "GMW000000000006", 1, date(2026, 11, 28)))

    assert actions == []
    assert errors == ["E: datum 2026-11-28 ligt in de toekomst."]


def test_default_date_in_future_is_refused():
    actions, errors = run(A, B, default=date(2026, 12, 1))

    assert actions == []
    assert errors == ["event_date 2026-12-01 ligt in de toekomst."]


def test_date_before_start_of_network_is_refused():
    actions, errors = run(A, B, point("E", "GMW000000000006", 1, date(2019, 12, 31)))

    assert actions == []
    assert errors == [
        "E: datum 2019-12-31 ligt vóór de begindatum van het meetnet (2020-01-01)."
    ]


def test_closed_network_is_refused():
    closed = parse_gmn_response(
        (XML_DIR / "GMN000000000081.xml").read_text(encoding="utf-8")
    )

    actions, errors = run(point("X", "GMW000000000006", 1), gmn=closed)

    assert actions == []
    assert errors == [
        "GMN000000000081 is in de BRO al afgesloten op 2021-10-11. "
        "Er kunnen geen meetpunten meer bij of af."
    ]


def test_all_errors_are_reported_at_once():
    future = point("E", "GMW000000000006", 1, event_date=date(2027, 1, 1))

    actions, errors = run(A, A, B, future)

    assert actions == []
    assert len(errors) == 2


def test_end_date_ends_point_on_that_date():
    actions, errors = run(A, point("B", end_date=date(2026, 11, 20)))

    assert errors == []
    assert actions == [
        Action(
            registration_type="GMN_MeasuringPointEndDate",
            measuring_point_code="B",
            event_date=date(2026, 11, 20),
        )
    ]
