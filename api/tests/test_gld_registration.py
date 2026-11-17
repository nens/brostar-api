"""Tests for GLD registration measurement rules and period splitting."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.bro_upload.upload_datamodels import GLDAddition, TimeValuePair
from api.corrections.exceptions import CorrectionValidationError
from api.corrections.gld.registration import (
    build_segment_addition,
    fetch_tube_geometry,
    split_measurements,
)
from api.corrections.gld.serializers import GLDRegistrationSerializer
from api.corrections.gld.validation import (
    ValidationSettings,
    validate_measurements,
)
from api.models import UploadTask
from api.tests import fixtures

XML_DIR = Path(__file__).parent / "xml_strings"
GLD_XML = (XML_DIR / "gld_correction_GLD000000000024.xml").read_text(encoding="utf-8")
GMW_XML = (XML_DIR / "GMW000000048905.xml").read_text(encoding="utf-8")
organisation = fixtures.organisation
user = fixtures.user
userprofile = fixtures.userprofile


def _time_value_pairs(times: list[str], values: list[float | None] | None = None):
    values = values or [1.0] * len(times)
    return [TimeValuePair(time=time, value=value) for time, value in zip(times, values)]


def _addition(
    measurements: list[TimeValuePair],
    instrument_type: str = "druksensor",
) -> GLDAddition:
    return GLDAddition(
        investigator_kvk="12345678",
        observation_type="reguliereMeting",
        evaluation_procedure="onbekend",
        measurement_instrument_type=instrument_type,
        process_reference="NEN5120v1991",
        begin_position="2021-01-01",
        end_position="2021-01-01",
        time_value_pairs=measurements,
    )


def test_split_measurements_uses_one_day_for_fewer_than_fifty_values():
    measurements = _time_value_pairs(
        [
            "2021-01-01T00:00:00+00:00",
            "2021-01-02T00:00:00+00:00",
            "2021-01-04T00:00:00+00:00",
        ]
    )

    segments = split_measurements(_addition(measurements))

    assert [[item.time for item in segment] for segment in segments] == [
        ["2021-01-01T00:00:00+00:00", "2021-01-02T00:00:00+00:00"],
        ["2021-01-04T00:00:00+00:00"],
    ]


def test_split_measurements_infers_and_caps_interval_for_fifty_values():
    start = datetime(2021, 1, 1)
    times = [(start + timedelta(days=index * 2)).isoformat() for index in range(49)]
    times.append((start + timedelta(days=48 * 2 + 25)).isoformat())

    segments = split_measurements(_addition(_time_value_pairs(times)))

    assert [len(segment) for segment in segments] == [49, 1]


def test_peilklokje_measurements_are_not_split():
    measurements = _time_value_pairs(["2021-01-01T00:00:00", "2021-02-01T00:00:00"])

    assert len(split_measurements(_addition(measurements, "analoogPeilklokje"))) == 1


def test_segment_addition_generates_ids_and_recalculates_derived_period():
    addition = _addition(
        _time_value_pairs(["2021-01-02T01:00:00+01:00", "2021-01-01T23:00:00+01:00"])
    )
    segment = split_measurements(addition)[0]

    first = build_segment_addition(addition, segment)
    second = build_segment_addition(addition, segment)

    assert first.begin_position == "2021-01-01"
    assert first.end_position == "2021-01-02"
    assert first.result_time == "2021-01-02T01:00:00+01:00"
    assert first.time_value_pairs[0].time == "2021-01-01T23:00:00+01:00"
    assert {
        first.observation_id,
        first.observation_process_id,
        first.measurement_timeseries_id,
    }.isdisjoint(
        {
            second.observation_id,
            second.observation_process_id,
            second.measurement_timeseries_id,
        }
    )
    assert first.process_reference == addition.process_reference


def test_validation_applies_physical_tolerance_and_preserves_null_status():
    measurements = _time_value_pairs(
        [
            "2021-01-01T00:00:00",
            "2021-01-01T01:00:00",
            "2021-01-01T02:00:00",
            "2021-01-01T03:00:00",
        ],
        [9.95, 9.8, 10.2, None],
    )
    measurements[3].status_quality_control = "afgekeurd"

    validate_measurements(
        measurements,
        ValidationSettings(rules=("below_tube_top",), tube_top_tolerance=0.1),
        tube_top=10.0,
    )

    assert measurements[0].status_quality_control == "onbeslist"
    assert measurements[1].status_quality_control == "goedgekeurd"
    assert measurements[2].status_quality_control == "afgekeurd"
    assert measurements[3].status_quality_control == "afgekeurd"


def test_validation_applies_tube_bottom_and_optional_sensor_rules():
    measurements = _time_value_pairs(
        [
            "2021-01-01T00:00:00",
            "2021-01-01T01:00:00",
            "2021-01-01T02:00:00",
            "2021-01-01T03:00:00",
        ],
        [-9.95, 0.0, -10.2, 1.0],
    )
    settings = ValidationSettings(
        rules=("above_tube_bottom", "at_or_below_sensor_height"),
        tube_bottom_tolerance=0.1,
        sensor_height=1.0,
    )

    validate_measurements(measurements, settings, tube_bottom=-10.0)

    assert measurements[0].status_quality_control == "onbeslist"
    assert measurements[1].status_quality_control == "goedgekeurd"
    assert measurements[2].status_quality_control == "afgekeurd"
    assert measurements[3].status_quality_control == "onbeslist"


def test_validation_marks_flatline_and_spike_anomalies():
    flatline = _time_value_pairs(
        [f"2021-01-01T{hour:02d}:00:00" for hour in range(7)],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0],
    )
    validate_measurements(flatline, ValidationSettings(rules=("flatline",)))
    assert all(item.status_quality_control == "afgekeurd" for item in flatline[:6])

    spike_values = [0.0] * 14 + [10.0, 10.0]
    spikes = _time_value_pairs(
        [f"2021-01-01T{hour:02d}:00:00" for hour in range(len(spike_values))],
        spike_values,
    )
    validate_measurements(spikes, ValidationSettings(rules=("spike",)))
    assert spikes[14].status_quality_control == "afgekeurd"


# I want to test realistic values, where we have a gradual flow, then reach 4.5, at which it flatlines for 10 measurements, to then gradually rise.
def test_validation_marks_flatline_realistic():
    flatline = _time_value_pairs(
        [f"2021-01-01T{hour:02d}:00:00" for hour in range(21)],
        [
            5.0,
            4.95,
            4.93,
            4.7,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.5,
            4.55,
            4.5,
            4.6,
            4.8,
            12,
            4.9,
            4.94,
            5,
        ],
    )
    validate_measurements(flatline, ValidationSettings(rules=("flatline",)))

    assert all(item.status_quality_control == "afgekeurd" for item in flatline[4:8])

    validate_measurements(flatline, ValidationSettings(rules=("spike",)))
    assert flatline[18].status_quality_control == "afgekeurd"


def test_fetch_tube_geometry_follows_the_gld_monitoring_point(monkeypatch):
    from api.corrections.gld import registration

    get_text = mock.Mock(side_effect=[GLD_XML, GMW_XML])
    monkeypatch.setattr(registration, "get_text", get_text)

    assert fetch_tube_geometry("GLD000000000024") == (-0.57, -4.41)
    assert get_text.call_args_list == [
        mock.call("/gm/gld/v1/objects/GLD000000000024"),
        mock.call(
            "/gm/gmw/v1/objects/GMW000000046948",
            params={"fullHistory": "nee"},
        ),
    ]


def test_fetch_tube_geometry_rejects_invalid_bro_id_before_request(monkeypatch):
    from api.corrections.gld import registration

    get_text = mock.Mock()
    monkeypatch.setattr(registration, "get_text", get_text)

    with pytest.raises(CorrectionValidationError):
        fetch_tube_geometry("../not-a-gld-id")

    get_text.assert_not_called()


def test_registration_serializer_rejects_client_generated_ids():
    serializer = GLDRegistrationSerializer(
        data={
            "project_number": "1255",
            "metadata": {
                "requestReference": "test-registration",
                "qualityRegime": "IMBRO",
            },
            "sourcedocument_data": {
                "observation_id": "caller-id",
                "investigator_kvk": "12345678",
                "observation_type": "reguliereMeting",
                "evaluation_procedure": "onbekend",
                "measurement_instrument_type": "druksensor",
                "process_reference": "NEN5120v1991",
                "begin_position": "2021-01-01",
                "end_position": "2021-01-01",
                "time_value_pairs": [{"time": "2021-01-01T00:00:00", "value": 1.0}],
            },
        }
    )

    assert not serializer.is_valid()
    assert "generated by the server" in str(serializer.errors)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db(transaction=True)
def test_registration_creates_one_task_per_segment(
    api_client, monkeypatch, user, userprofile, organisation
):
    from api import signals
    from api.corrections.gld import views

    monkeypatch.setattr(views, "fetch_tube_geometry", mock.Mock(return_value=(10, -10)))
    start_upload = mock.Mock()
    monkeypatch.setattr(signals.tasks, "upload_task", start_upload)
    user.refresh_from_db()
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("api:uploadtask-gld-registration"),
        {
            "project_number": "1255",
            "metadata": {
                "requestReference": "test-registration",
                "qualityRegime": "IMBRO",
                "broId": "GLD000000000024",
            },
            "sourcedocument_data": {
                "investigatorKvk": "12345678",
                "observationType": "reguliereMeting",
                "evaluationProcedure": "onbekend",
                "measurementInstrumentType": "druksensor",
                "processReference": "NEN5120v1991",
                "beginPosition": "2021-01-01",
                "endPosition": "2021-01-03",
                "timeValuePairs": [
                    {"time": "2021-01-01T00:00:00+00:00", "value": 1.0},
                    {"time": "2021-01-03T00:00:00+00:00", "value": 2.0},
                ],
            },
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert len(response.data["upload_tasks"]) == 2
    assert start_upload.call_count == 2
    tasks = list(UploadTask.objects.order_by("created"))
    assert len(tasks) == 2
    assert tasks[0].sourcedocument_data["beginPosition"] == "2021-01-01"
    assert tasks[1].sourcedocument_data["beginPosition"] == "2021-01-03"
    for identifier in (
        "observationId",
        "observationProcessId",
        "measurementTimeseriesId",
    ):
        assert (
            tasks[0].sourcedocument_data[identifier]
            != tasks[1].sourcedocument_data[identifier]
        )
    assert (
        tasks[0].metadata["requestReference"] != tasks[1].metadata["requestReference"]
    )
    assert (
        tasks[0].sourcedocument_data["timeValuePairs"][0]["statusQualityControl"]
        == "goedgekeurd"
    )
    assert tasks[0].data_owner == organisation
    assert response.data["upload_tasks"][0]["uuid"] == str(tasks[0].uuid)


@pytest.mark.django_db
def test_registration_rejects_caller_supplied_ids(api_client, user, userprofile):
    user.refresh_from_db()
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("api:uploadtask-gld-registration"),
        {
            "project_number": "1255",
            "metadata": {
                "requestReference": "test-registration",
                "qualityRegime": "IMBRO",
                "broId": "GLD000000000024",
            },
            "sourcedocument_data": {
                "observationId": "caller-id",
                "investigatorKvk": "12345678",
                "observationType": "reguliereMeting",
                "evaluationProcedure": "onbekend",
                "measurementInstrumentType": "druksensor",
                "processReference": "NEN5120v1991",
                "timeValuePairs": [{"time": "2021-01-01T00:00:00", "value": 1.0}],
            },
        },
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert UploadTask.objects.count() == 0
