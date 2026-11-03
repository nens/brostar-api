"""Unit tests for the GLD correction helpers (no database involved)."""

import json
from pathlib import Path

import pytest
from rest_framework.exceptions import APIException

from api.corrections.exceptions import CorrectionValidationError
from api.corrections.gld import timespan
from api.corrections.gld.builder import build_addition, build_metadata
from api.corrections.gld.matching import find_matches, seconds_between, single_match
from api.corrections.gld.merging import (
    measurement_from_payload,
    merge_measurements,
    merge_procedure,
)
from api.corrections.gld.xml_reader import Measurement, parse_gld_response
from api.corrections.kvk import resolve_investigator_kvk

XML_DIR = Path(__file__).parent / "xml_strings"
GLD_XML = (XML_DIR / "gld_correction_GLD000000000024.xml").read_text(encoding="utf-8")
GLD_SUMMARIES = json.loads(
    (XML_DIR / "gld_correction_GLD000000000024_summaries.json").read_text(
        encoding="utf-8"
    )
)


@pytest.fixture
def parsed():
    return parse_gld_response(GLD_XML)


# --------------------------------------------------------------------- reader


def test_parse_document_level(parsed):
    assert parsed.bro_id == "GLD000000000024"
    assert parsed.quality_regime == "IMBRO/A"
    assert parsed.delivery_accountable_party == "20164929"
    assert len(parsed.observations) == 3


def test_parse_observation_details(parsed):
    observation = parsed.get_observation("observationId_001")

    assert observation.observation_process_id == "ObservationProcessId_001"
    assert observation.measurement_timeseries_id == "measurementTimeseriesId_001"
    assert observation.observation_type == "reguliereMeting"
    assert observation.validation_status == "onbekend"
    assert observation.begin_position == "2021-01-04"
    assert observation.end_position == "2021-01-08"
    assert observation.result_time == "2021-01-08T12:00:00+01:00"
    assert observation.date_stamp == "2021-01-04"
    assert observation.process_reference == "NEN5120v1991"
    assert observation.evaluation_procedure == "onbekend"
    assert observation.measurement_instrument_type == "onbekend"
    assert observation.air_pressure_compensation_type is None
    assert observation.repeat_procedure is False
    assert len(observation.measurements) == 5


def test_parse_measurements(parsed):
    measurements = parsed.get_observation("observationId_001").measurements

    assert measurements[0].time == "2021-01-04T12:00:00+01:00"
    assert measurements[0].value == 0.52
    assert measurements[0].status_quality_control == "onbekend"

    censored = measurements[-1]
    assert censored.value is None
    assert censored.censor_reason == "kleinerDanLimietwaarde"
    assert censored.censoring_limitvalue == -0.2
    assert censored.status_quality_control == "afgekeurd"


def test_parse_air_pressure_compensation(parsed):
    observation = parsed.get_observation("observationId_002")
    assert observation.air_pressure_compensation_type == "KNMImeting"
    assert observation.evaluation_procedure == "oordeelDeskundige"


def test_parse_referenced_procedure(parsed):
    observation = parsed.get_observation("observationId_003")

    assert observation.repeat_procedure is True
    assert observation.observation_process_id == "ObservationProcessId_002"
    assert observation.observation_type == "controlemeting"
    assert observation.validation_status is None


def test_unknown_observation_returns_none(parsed):
    assert parsed.get_observation("observationId_999") is None


def test_parse_invalid_xml():
    with pytest.raises(CorrectionValidationError):
        parse_gld_response("<not-xml")


# ------------------------------------------------------------------- matching


def test_seconds_between_handles_offsets():
    assert (
        seconds_between("2021-01-04T12:00:00+01:00", "2021-01-04T11:00:00+00:00") == 0
    )


def test_find_matches_exact_only():
    times = ["2021-01-04T12:00:00+01:00", "2021-01-05T12:00:00+01:00"]

    assert find_matches(times, "2021-01-05T12:00:00+01:00") == [1]
    assert find_matches(times, "2021-01-05T12:02:00+01:00") == []


def test_find_matches_within_delta_t_sorted_by_distance():
    times = [
        "2021-01-04T12:00:00+01:00",
        "2021-01-04T12:10:00+01:00",
        "2021-01-05T12:00:00+01:00",
    ]

    assert find_matches(times, "2021-01-04T12:08:00+01:00", delta_t=600) == [1, 0]


def test_single_match_raises_on_multiple():
    times = ["2021-01-04T12:00:00+01:00", "2021-01-04T12:10:00+01:00"]

    with pytest.raises(CorrectionValidationError) as error:
        single_match(times, "2021-01-04T12:05:00+01:00", delta_t=600)

    assert "delta_t" in str(error.value)


def test_parse_time_rejects_nonsense():
    with pytest.raises(CorrectionValidationError):
        seconds_between("gisteren", "2021-01-04T12:00:00+01:00")


# -------------------------------------------------------------------- merging


def test_merge_measurements_replaces_exact_match():
    existing = [
        Measurement(time="2021-01-04T12:00:00+01:00", value=0.52),
        Measurement(time="2021-01-05T12:00:00+01:00", value=0.55),
    ]
    incoming = [Measurement(time="2021-01-05T12:00:00+01:00", value=0.99)]

    merged, changed, log = merge_measurements(existing, incoming)

    assert changed == 1
    assert [item.value for item in merged] == [0.52, 0.99]
    assert "vervangen" in log[0]


def test_merge_measurements_adds_and_sorts():
    existing = [
        Measurement(time="2021-01-04T12:00:00+01:00", value=0.52),
        Measurement(time="2021-01-06T12:00:00+01:00", value=0.58),
    ]
    incoming = [Measurement(time="2021-01-05T12:00:00+01:00", value=0.55)]

    merged, changed, _ = merge_measurements(existing, incoming)

    assert changed == 1
    assert [item.time for item in merged] == [
        "2021-01-04T12:00:00+01:00",
        "2021-01-05T12:00:00+01:00",
        "2021-01-06T12:00:00+01:00",
    ]


def test_merge_measurements_within_delta_t_overwrites_time():
    existing = [Measurement(time="2021-01-05T12:00:00+01:00", value=0.55)]
    incoming = [Measurement(time="2021-01-05T12:02:00+01:00", value=0.56)]

    merged, changed, _ = merge_measurements(existing, incoming, delta_t=300)

    assert changed == 1
    assert len(merged) == 1
    assert merged[0].time == "2021-01-05T12:02:00+01:00"


def test_merge_measurements_identical_is_no_change():
    existing = [Measurement(time="2021-01-05T12:00:00+01:00", value=0.55)]
    incoming = [Measurement(time="2021-01-05T12:00:00+01:00", value=0.55)]

    merged, changed, log = merge_measurements(existing, incoming)

    assert changed == 0
    assert len(merged) == 1
    assert "niets gewijzigd" in log[0]


def test_merge_procedure_only_touches_given_fields():
    existing = {
        "process_reference": "NEN5120v1991",
        "evaluation_procedure": "onbekend",
        "measurement_instrument_type": "onbekend",
    }
    updates = {
        "evaluation_procedure": "brabantWater2013",
        "measurement_instrument_type": "onbekend",
    }

    merged, changed, log = merge_procedure(existing, updates)

    assert changed == 1
    assert merged["evaluation_procedure"] == "brabantWater2013"
    assert merged["process_reference"] == "NEN5120v1991"
    assert any("niets gewijzigd" in line for line in log)


def test_measurement_from_payload_defaults():
    measurement = measurement_from_payload(
        {"time": "2021-01-05T12:00:00+01:00", "value": 0.55}
    )

    assert measurement.status_quality_control == "onbekend"
    assert measurement.censor_reason is None


# ------------------------------------------------------------------- timespan


def test_times_outside_period(parsed):
    observation = parsed.get_observation("observationId_001")
    measurements = [
        Measurement(time="2021-01-08T23:00:00+01:00", value=0.1),
        Measurement(time="2021-01-09T12:00:00+01:00", value=0.1),
    ]

    outside = timespan.times_outside_period(observation, measurements)

    assert [item.time for item in outside] == ["2021-01-09T12:00:00+01:00"]


def test_assert_best_fitting_observation_accepts_when_closest(parsed):
    observation = parsed.get_observation("observationId_002")

    timespan.assert_best_fitting_observation(
        observation,
        GLD_SUMMARIES,
        Measurement(time="2021-04-10T12:00:00+02:00", value=1.2),
    )


def test_assert_best_fitting_observation_rejects_when_other_is_closer(parsed):
    observation = parsed.get_observation("observationId_001")

    with pytest.raises(CorrectionValidationError) as error:
        timespan.assert_best_fitting_observation(
            observation,
            GLD_SUMMARIES,
            Measurement(time="2021-03-28T12:00:00+02:00", value=1.1),
        )

    assert "observationId_002" in str(error.value)


def test_assert_best_fitting_ignores_other_observation_types(parsed):
    """A controlemeting nearby may not block a reguliereMeting correction."""
    observation = parsed.get_observation("observationId_002")

    timespan.assert_best_fitting_observation(
        observation,
        GLD_SUMMARIES,
        Measurement(time="2021-05-17T12:00:00+02:00", value=1.2),
    )


def test_recalculate_period():
    measurements = [
        Measurement(time="2021-01-09T12:00:00+01:00", value=0.1),
        Measurement(time="2021-01-04T12:00:00+01:00", value=0.2),
    ]

    begin, end, result_time = timespan.recalculate_period(measurements)

    assert begin == "2021-01-04"
    assert end == "2021-01-09"
    assert result_time == "2021-01-09T12:00:00+01:00"


# ------------------------------------------------------------------------ kvk


class _Organisation:
    kvk_number = "12345678"


class _Profile:
    organisation = _Organisation()


class _User:
    userprofile = _Profile()


def test_resolve_kvk_prefers_explicit():
    kvk, log = resolve_investigator_kvk(
        user=_User(),
        explicit_kvk="99999999",
        use_organisation_kvk=True,
        delivery_accountable_party="20164929",
    )

    assert kvk == "99999999"
    assert "request" in log


def test_resolve_kvk_uses_organisation_when_requested():
    kvk, log = resolve_investigator_kvk(
        user=_User(),
        explicit_kvk=None,
        use_organisation_kvk=True,
        delivery_accountable_party="20164929",
    )

    assert kvk == "12345678"
    assert "organisatie" in log


def test_resolve_kvk_falls_back_to_accountable_party():
    kvk, log = resolve_investigator_kvk(
        user=_User(),
        explicit_kvk=None,
        use_organisation_kvk=False,
        delivery_accountable_party="20164929",
    )

    assert kvk == "20164929"
    assert "deliveryAccountableParty" in log


def test_resolve_kvk_without_any_source():
    with pytest.raises(CorrectionValidationError):
        resolve_investigator_kvk(
            user=_User(),
            explicit_kvk=None,
            use_organisation_kvk=False,
            delivery_accountable_party=None,
        )


# -------------------------------------------------------------------- builder


def test_build_metadata(parsed):
    metadata = build_metadata(parsed, "eigenCorrectie").model_dump(by_alias=True)

    assert metadata["broId"] == "GLD000000000024"
    assert metadata["qualityRegime"] == "IMBRO/A"
    assert metadata["deliveryAccountableParty"] == "20164929"
    assert metadata["correctionReason"] == "eigenCorrectie"
    assert metadata["requestReference"].startswith("GLD_Addition_correction_")


def test_build_addition_reuses_identifiers(parsed):
    observation = parsed.get_observation("observationId_001")

    addition = build_addition(
        observation=observation,
        procedure=observation.procedure(),
        measurements=observation.measurements,
        investigator_kvk="20164929",
        begin_position="2021-01-04",
        end_position="2021-01-08",
        result_time="2021-01-08T12:00:00+01:00",
    ).model_dump(mode="json", by_alias=True)

    assert addition["observationId"] == "observationId_001"
    assert addition["observationProcessId"] == "ObservationProcessId_001"
    assert addition["measurementTimeseriesId"] == "measurementTimeseriesId_001"
    assert addition["investigatorKvk"] == "20164929"
    assert addition["validationStatus"] == "onbekend"
    assert len(addition["timeValuePairs"]) == 5
    assert addition["timeValuePairs"][-1]["censorReason"] == "kleinerDanLimietwaarde"


def test_build_addition_without_timeseries_id(parsed):
    observation = parsed.get_observation("observationId_001")
    observation.measurement_timeseries_id = None

    with pytest.raises(APIException):
        build_addition(
            observation=observation,
            procedure=observation.procedure(),
            measurements=observation.measurements,
            investigator_kvk="20164929",
            begin_position="2021-01-04",
            end_position="2021-01-08",
            result_time=None,
        )
