from datetime import UTC, date, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

# Assume your models are imported here, like:
from api.bro_upload.upload_datamodels import (
    Analysis,
    AnalysisProcess,
    FieldResearch,
    GLDAddition,
    GMWLengthening,
    GMWMaintainer,
    GMWOwner,
    MonitoringTubeLengthening,
    MonitoringTubePositions,
    TimeValuePair,
    UploadTask,
    UploadTaskMetadata,
)


def test_field_research_defaults():
    research = FieldResearch(
        sampling_standard="NEN5740",
        sampling_date_time=datetime(2023, 10, 1, 12, 30, 30),
    )
    assert research.sample_aerated == "onbekend"
    assert research.sampling_standard == "NEN5740"
    # Corrected to ISO format string
    assert research.sampling_date_time == "2023-10-01T12:30:30"
    assert research.hose_reused == "onbekend"

    utc_time = datetime(2023, 10, 1, 12, 30, 30, tzinfo=UTC)
    research_utc = FieldResearch(
        sampling_standard="NEN5740",
        sampling_date_time=utc_time,
    )
    assert research_utc.sampling_date_time == "2023-10-01T12:30:30+00:00"


def test_analysis_process_defaults():
    process = AnalysisProcess(
        analytical_technique="wateranalyse",
        date=date(2023, 10, 2),
        valuation_method="handmatig",
        analyses=[
            Analysis(
                parameter=123,
                unit="mg/L",
                analysis_measurement_value=1.23,
                limit_symbol=None,
                reporting_limit=None,
                quality_control_status="valid",
            )
        ],
    )
    assert process.analytical_technique == "wateranalyse"
    assert process.date == "2023-10-02"
    assert process.valuation_method == "handmatig"
    assert len(process.analyses) == 1


def test_upload_task_metadata_valid():
    metadata = UploadTaskMetadata(
        request_reference="REQ123",
        delivery_accountable_party="Some Party",
        quality_regime="IMBRO",
        bro_id="BRO123",
        correction_reason="eigenCorrectie",
    )
    assert metadata.request_reference == "REQ123"
    assert metadata.delivery_accountable_party == "Some Party"
    assert metadata.model_dump(by_alias=True)["requestReference"] == "REQ123"


def test_upload_task_metadata_missing_required():
    with pytest.raises(ValidationError):
        UploadTaskMetadata(
            request_reference="REQ123",
            delivery_accountable_party=None,
            # missing required field 'quality_regime'
        )


def test_monitoring_tube_lengthening_defaults():
    tube = MonitoringTubeLengthening(
        tube_number=1,
        tube_top_position=10.5,
        tube_top_positioning_method="0tot2cmwaterpassing",
        plain_tube_part_length=5.0,
    )
    assert tube.variable_diameter is None
    assert tube.model_dump(by_alias=True)["tubeNumber"] == 1


def test_gmw_lengthening_with_monitoring_tubes():
    tube = MonitoringTubeLengthening(
        tube_number=1,
        tube_top_position=10.5,
        tube_top_positioning_method="0tot2cmwaterpassing",
        plain_tube_part_length=5.0,
    )
    event = GMWLengthening(
        event_date="2023-10-01",
        monitoring_tubes=[tube],
    )
    assert event.event_date == "2023-10-01"
    assert len(event.monitoring_tubes) == 1


def test_gmw_lengthening_camel_case():
    camel_case_input = {
        "eventDate": "2023-10-01",
        "monitoringTubes": [
            {
                "tubeNumber": 1,
                "tubeTopPosition": 10.5,
                "tubeTopPositioningMethod": "0tot2cmwaterpassing",
                "plainTubePartLength": 5.0,
            }
        ],
    }
    event = GMWLengthening(**camel_case_input)
    assert event.event_date == "2023-10-01"
    assert len(event.monitoring_tubes) == 1


def test_gmw_lengthening_with_well_head_protector():
    event = GMWLengthening(
        event_date="2023-10-01",
        well_head_protector="potKoker",
        monitoring_tubes=[],
    )
    assert event.event_date == "2023-10-01"
    assert len(event.monitoring_tubes) == 0


def test_gmw_maintainer():
    event = GMWMaintainer(
        event_date="2023-10-01", maintenance_responsible_party="MaintainerCorp"
    )
    assert event.maintenance_responsible_party == "MaintainerCorp"


def test_gmw_owner():
    event = GMWOwner(event_date="2023-10-01", owner="OwnerCorp")
    assert event.owner == "OwnerCorp"


def test_monitoring_tube_positions():
    pos = MonitoringTubePositions(
        tube_number=1, tube_top_position=12.5, tube_top_positioning_method="Surveyed"
    )
    assert pos.tube_top_position == 12.5
    assert pos.model_dump(by_alias=True)["tubeTopPositioningMethod"] == "Surveyed"


def test_upload_task_valid():
    metadata = UploadTaskMetadata(
        request_reference="REQ123",
        delivery_accountable_party=None,
        quality_regime="IMBRO",
        bro_id=None,
        correction_reason=None,
    )
    task = UploadTask(
        bro_domain="GMW",
        project_number="PN123",
        registration_type="GMW_Construction",
        request_type="registration",
        sourcedocument_data={"dummy": "data"},
        metadata=metadata,
    )
    assert task.bro_domain == "GMW"
    assert task.model_dump()["metadata"]["request_reference"] == "REQ123"


def test_upload_task_invalid_bro_domain():
    metadata = UploadTaskMetadata(
        request_reference="REQ123",
        delivery_accountable_party=None,
        quality_regime="IMBRO",
        bro_id=None,
        correction_reason=None,
    )
    with pytest.raises(ValidationError):
        UploadTask(
            bro_domain="INVALID",
            project_number="PN123",
            registration_type="GMW_Construction",
            request_type="registration",
            sourcedocument_data={"dummy": "data"},
            metadata=metadata,
        )


def test_time_value_pair_valid_datetime():
    dt = datetime(2024, 1, 1, 12, 30)
    pair = TimeValuePair(time=dt, value=10.5)
    # Ensure time got converted to ISO format string
    assert isinstance(pair.time, str)
    assert pair.time.startswith("2024-01-01T12:30")
    assert pair.value == 10.5
    assert pair.status_quality_control == "onbekend"


def test_time_value_pair_valid_string():
    pair = TimeValuePair(time="2024-01-01T12:30:00", value=5.5)
    assert pair.time == "2024-01-01T12:30:00"


def test_time_value_pair_val_str_to_float():
    pair = TimeValuePair(time="2024-01-01T12:30:00", value="7.5")
    assert pair.time == "2024-01-01T12:30:00"
    assert pair.value == 7.5


def test_gld_addition_auto_generate_ids():
    gld = GLDAddition(
        investigator_kvk="12345678",
        observation_type="reguliereMeting",
        evaluation_procedure="ProcedureA",
        measurement_instrument_type="InstrumentX",
        air_pressure_compensation_type="None",
        process_reference="PR123",
        begin_position="2024-01-01T00:00:00",
        end_position="2024-01-02T00:00:00",
        time_value_pairs=[TimeValuePair(time="2024-01-01T12:00:00", value=10.0)],
    )
    # The fields should have been auto-populated with a UUID string
    assert gld.observation_id.startswith("_")
    assert gld.observation_process_id.startswith("_")
    assert gld.measurement_timeseries_id.startswith("_")
    assert gld.air_pressure_compensation_type is None

    # Validate that the auto-generated parts after _ are valid UUIDs
    UUID(gld.observation_id[1:])  # will raise if invalid
    UUID(gld.observation_process_id[1:])
    UUID(gld.measurement_timeseries_id[1:])

    # Validate if air pressure is set to None
    gld = GLDAddition(
        investigator_kvk="12345678",
        observation_type="reguliereMeting",
        evaluation_procedure="ProcedureA",
        measurement_instrument_type="InstrumentX",
        air_pressure_compensation_type="monitoringsnetmeting",
        process_reference="PR123",
        begin_position="2024-01-01T00:00:00",
        end_position="2024-01-02T00:00:00",
        time_value_pairs=[TimeValuePair(time="2024-01-01T12:00:00", value=10.0)],
    )
    assert gld.air_pressure_compensation_type is None

    # Validate if air pressure is kept correctly
    gld = GLDAddition(
        investigator_kvk="12345678",
        observation_type="reguliereMeting",
        evaluation_procedure="ProcedureA",
        measurement_instrument_type="druksensor",
        air_pressure_compensation_type="monitoringsnetmeting",
        process_reference="PR123",
        begin_position="2024-01-01T00:00:00",
        end_position="2024-01-02T00:00:00",
        time_value_pairs=[TimeValuePair(time="2024-01-01T12:00:00", value=10.0)],
    )
    assert gld.air_pressure_compensation_type == "monitoringsnetmeting"


def test_gld_addition_validation_status_reguliere_meting():
    gld = GLDAddition(
        investigator_kvk="12345678",
        observation_type="reguliereMeting",
        evaluation_procedure="ProcedureA",
        measurement_instrument_type="InstrumentX",
        process_reference="PR123",
        begin_position="2024-01-01T00:00:00",
        end_position="2024-01-02T00:00:00",
        time_value_pairs=[TimeValuePair(time="2024-01-01T12:00:00", value=10.0)],
    )
    assert gld.validation_status == "onbekend"


def test_gld_addition_validation_status_controlemeting():
    gld = GLDAddition(
        investigator_kvk="12345678",
        observation_type="controlemeting",
        evaluation_procedure="ProcedureB",
        measurement_instrument_type="InstrumentY",
        process_reference="PR456",
        begin_position="2024-02-01T00:00:00",
        end_position="2024-02-02T00:00:00",
        time_value_pairs=[TimeValuePair(time="2024-02-01T12:00:00", value=12.0)],
    )
    assert gld.validation_status is None


def test_gld_addition_missing_required_field():
    with pytest.raises(ValidationError):
        GLDAddition(
            # Missing investigator_kvk and others
            observation_type="controlemeting",
            evaluation_procedure="ProcedureB",
            measurement_instrument_type="InstrumentY",
            process_reference="PR456",
            begin_position="2024-02-01T00:00:00",
            end_position="2024-02-02T00:00:00",
            time_value_pairs=[TimeValuePair(time="2024-02-01T12:00:00", value=12.0)],
        )


def test_time_value_pair_missing_time():
    with pytest.raises(ValidationError):
        TimeValuePair(value=10.0)  # Missing 'time'
