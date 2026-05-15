# tests/test_signals.py
import pytest

from api.models import UploadTask
from api.tests.fixtures import (  # noqa: F401
    frd,
    geo_electric_measurement,
    gld,
    gmn,
    gmw,
    intermediate_event,
    measurement_configuration,
    measuringpoint,
    observation,
    organisation,
    tube,
)
from frd.models import FRD, GeoElectricMeasurement, MeasurementConfiguration
from gld.models import GLD, Observation  # Example model to check side effects
from gmn.models import GMN, IntermediateEvent, Measuringpoint
from gmw.models import GMW, Event, MonitoringTube  # Example model to check side effects

from ..models import Organisation


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_create_objects_gmw(organisation: Organisation):  # noqa: F811
    """
    Test that saving an UploadTask with status COMPLETED calls create_objects.
    We don’t mock, so we directly check the side effects on the database.
    """
    # 2. Create a completed UploadTask
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMW",
        registration_type="GMW_Construction",
        request_type="registration",
        status="COMPLETED",
        bro_id="BRO123",
        metadata={
            "qualityRegime": "IMBRO/A",
            "requestReference": "BROSTAR_Request",
            "deliveryAccountableParty": "50616641",
        },
        sourcedocument_data={
            "owner": "51468751",
            "offset": "0",
            "nitgCode": "B12A1234",
            "eventDate": "2025-09-08",
            "verticalDatum": "NAP",
            "wellStability": "stabielNAP",
            "deliveryContext": "KRW",
            "initialFunction": "kwaliteit",
            "monitoringTubes": [
                {
                    "glue": "geen",
                    "tubeType": "standaardbuis",
                    "tubeNumber": 1,
                    "tubeStatus": "gebruiksklaar",
                    "geoOhmCables": [],
                    "screenLength": 1,
                    "sockMaterial": "geen",
                    "tubeMaterial": "ijzer",
                    "tubeTopDiameter": 32,
                    "tubeTopPosition": 0,
                    "variableDiameter": "nee",
                    "sedimentSumpLength": None,
                    "plainTubePartLength": 1,
                    "sedimentSumpPresent": "nee",
                    "tubePackingMaterial": "filtergrind",
                    "numberOfGeoOhmCables": 0,
                    "artesianWellCapPresent": "ja",
                    "tubeTopPositioningMethod": "afgeleidSbl",
                }
            ],
            "deliveredLocation": "250000 450000",
            "groundLevelStable": "nee",
            "wellHeadProtector": "kokerMetaal",
            "constructionStandard": "onbekend",
            "wellConstructionDate": "2025-09-02",
            "numberOfMonitoringTubes": 1,
            "objectIdAccountableParty": "test_upload",
            "horizontalPositioningMethod": "RTKGPS2tot5cm",
            "maintenanceResponsibleParty": "51181584",
            "groundLevelPositioningMethod": "waterpassing0tot2cm",
        },
    )

    # 3. Since post_save signal should have fired,
    #    we check whether create_objects did its work.
    #    Here you should assert on the *real side effects* of create_objects.
    #    For example, if create_objects makes DB entries:
    assert GMW.objects.filter(bro_id="BRO123").exists()

    gmw = GMW.objects.get(bro_id="BRO123")  # noqa: F811
    assert gmw.well_construction_date == "2025-09-02"
    assert gmw.nitg_code == "B12A1234"
    assert gmw.internal_id == "test_upload"

    assert MonitoringTube.objects.filter(gmw=gmw).exists()

    monitoring_tube = MonitoringTube.objects.get(gmw=gmw)
    assert int(monitoring_tube.tube_number) == 1
    assert monitoring_tube.tube_material == "ijzer"
    assert monitoring_tube.tube_type == "standaardbuis"
    assert int(monitoring_tube.tube_top_diameter) == 32
    assert monitoring_tube.geo_ohm_cables == []

    assert monitoring_tube.tube_top_position == "0"
    assert monitoring_tube.plain_tube_part_length == "1"
    assert monitoring_tube.screen_top_position == "-1.0"  # 0 - 1 = -1
    assert monitoring_tube.screen_bottom_position == "-2.0"  # 0 -1 - 1 = -2


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_create_objects_gmw2(organisation: Organisation):  # noqa: F811
    """
    Test that saving an UploadTask with status COMPLETED calls create_objects.
    We don’t mock, so we directly check the side effects on the database.
    """
    # 2. Create a completed UploadTask
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMW",
        registration_type="GMW_Construction",
        request_type="registration",
        status="COMPLETED",
        bro_id="BRO123",
        metadata={
            "qualityRegime": "IMBRO/A",
            "requestReference": "BROSTAR_Request",
            "deliveryAccountableParty": "50616641",
        },
        sourcedocument_data={
            "owner": "51468751",
            "offset": "0",
            "nitgCode": "B12A1234",
            "eventDate": "2025-09-08",
            "verticalDatum": "NAP",
            "wellStability": "stabielNAP",
            "deliveryContext": "KRW",
            "initialFunction": "kwaliteit",
            "monitoringTubes": [
                {
                    "glue": "geen",
                    "tubeType": "standaardbuis",
                    "tubeNumber": 1,
                    "tubeStatus": "gebruiksklaar",
                    "screenLength": 1,
                    "sockMaterial": "geen",
                    "tubeMaterial": "ijzer",
                    "tubeTopDiameter": 32,
                    "tubeTopPosition": 0,
                    "variableDiameter": "nee",
                    "sedimentSumpLength": None,
                    "plainTubePartLength": 1,
                    "sedimentSumpPresent": "nee",
                    "tubePackingMaterial": "filtergrind",
                    "numberOfGeoOhmCables": 0,
                    "artesianWellCapPresent": "ja",
                    "tubeTopPositioningMethod": "afgeleidSbl",
                }
            ],
            "deliveredLocation": "250000 450000",
            "groundLevelStable": "nee",
            "wellHeadProtector": "kokerMetaal",
            "constructionStandard": "onbekend",
            "wellConstructionDate": "2025-09-02",
            "numberOfMonitoringTubes": 1,
            "objectIdAccountableParty": "test_upload",
            "horizontalPositioningMethod": "RTKGPS2tot5cm",
            "maintenanceResponsibleParty": "51181584",
            "groundLevelPositioningMethod": "waterpassing0tot2cm",
        },
    )

    # 3. Since post_save signal should have fired,
    #    we check whether create_objects did its work.
    #    Here you should assert on the *real side effects* of create_objects.
    #    For example, if create_objects makes DB entries:
    assert GMW.objects.filter(bro_id="BRO123").exists()

    gmw = GMW.objects.get(bro_id="BRO123")  # noqa: F811
    assert gmw.well_construction_date == "2025-09-02"
    assert gmw.nitg_code == "B12A1234"
    assert gmw.internal_id == "test_upload"
    assert gmw.standardized_location is not None

    assert MonitoringTube.objects.filter(gmw=gmw).exists()

    monitoring_tube = MonitoringTube.objects.get(gmw=gmw)
    assert int(monitoring_tube.tube_number) == 1
    assert monitoring_tube.tube_material == "ijzer"
    assert monitoring_tube.tube_type == "standaardbuis"
    assert int(monitoring_tube.tube_top_diameter) == 32
    assert monitoring_tube.geo_ohm_cables == []


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_create_objects_gld(organisation: Organisation):  # noqa: F811
    """
    Test that saving an UploadTask with status COMPLETED calls create_objects.
    We don’t mock, so we directly check the side effects on the database.
    """
    # 2. Create a completed UploadTask
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GLD",
        registration_type="GLD_StartRegistration",
        request_type="registration",
        status="COMPLETED",
        bro_id="GLD000000012345",
        metadata={
            "qualityRegime": "IMBRO/A",
            "requestReference": "BROSTAR_Request",
            "deliveryAccountableParty": "50616641",
        },
        sourcedocument_data={
            "objectIdAccountableParty": "test_upload",
            "gmwBroId": "BRO123",
            "tubeNumber": 1,
        },
    )

    # 3. Since post_save signal should have fired,
    #    we check whether create_objects did its work.
    #    Here you should assert on the *real side effects* of create_objects.
    #    For example, if create_objects makes DB entries:
    assert GLD.objects.filter(bro_id="GLD000000012345").exists()

    gld_instance = GLD.objects.get(bro_id="GLD000000012345")
    assert gld_instance.internal_id == "test_upload"
    assert gld_instance.bro_id == "GLD000000012345"
    assert gld_instance.gmw_bro_id == "BRO123"
    assert int(gld_instance.tube_number) == 1


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_create_objects_gld_observation(
    organisation: Organisation,  # noqa: F811
    gld: GLD,  # noqa: F811
):
    """
    Test that saving an UploadTask with status COMPLETED calls create_objects.
    We don’t mock, so we directly check the side effects on the database.
    """
    # 2. Create a completed UploadTask
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMN",
        registration_type="GLD_Addition",
        request_type="registration",
        status="COMPLETED",
        bro_id=gld.bro_id,
        metadata={
            "broId": "GLD000000098254",
            "qualityRegime": "IMBRO",
            "requestReference": "GLD000000098254: IMBRO controlemeting 2021-02-04T12:20:14Z-None (2025-10-01T20:41:20Z)",
            "deliveryAccountableParty": "08213234",
        },
        sourcedocument_data={
            "date": "2025-05-08",
            "resultTime": "2025-05-08T10:16:40+02:00",
            "endPosition": "2025-05-08",
            "beginPosition": "2021-08-23",
            "observationId": "_1ae0ebbf-4845-4237-aa68-f6a0c3b7e6bc",
            "timeValuePairs": [
                {
                    "time": "2025-02-05T13:38:31+01:00",
                    "value": 5.74,
                    "censorReason": None,
                    "censoringLimitvalue": None,
                    "statusQualityControl": "goedgekeurd",
                },
                {
                    "time": "2025-05-08T10:16:40+02:00",
                    "value": 5.2,
                    "censorReason": None,
                    "censoringLimitvalue": None,
                    "statusQualityControl": "goedgekeurd",
                },
            ],
            "investigatorKvk": "08213234",
            "observationType": "controlemeting",
            "processReference": "vitensMeetprotocolGrondwater",
            "validationStatus": None,
            "evaluationProcedure": "vitensBeoordelingsprotocolGrondwater",
            "observationProcessId": "_aca10522-1541-492e-bd6f-753112d58249",
            "measurementTimeseriesId": "_dfe508cf-862e-4b67-961a-45dcdd137f0d",
            "measurementInstrumentType": "elektronischPeilklokje",
            "airPressureCompensationType": None,
        },
    )

    assert GLD.objects.filter(bro_id=gld.bro_id).exists()
    assert Observation.objects.filter(gld=gld).exists()

    observation_object = Observation.objects.get(gld=gld)

    assert observation_object.observation_id == "_1ae0ebbf-4845-4237-aa68-f6a0c3b7e6bc"
    assert observation_object.begin_position.isoformat() == "2021-08-23"
    assert observation_object.end_position.isoformat() == "2025-05-08"
    assert observation_object.result_time.isoformat() == "2025-05-08T08:16:40+00:00"
    assert observation_object.investigator_kvk == "08213234"
    assert observation_object.observation_type == "controlemeting"
    assert observation_object.process_reference == "vitensMeetprotocolGrondwater"
    assert observation_object.measurement_instrument_type == "elektronischPeilklokje"


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_create_objects_gmn(organisation: Organisation):  # noqa: F811
    """
    Test that saving an UploadTask with status COMPLETED calls create_objects.
    We don’t mock, so we directly check the side effects on the database.
    """
    # 2. Create a completed UploadTask
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMN",
        registration_type="GMN_StartRegistration",
        request_type="registration",
        status="COMPLETED",
        bro_id="BRO123",
        metadata={
            "qualityRegime": "IMBRO/A",
            "requestReference": "BROSTAR_Request",
            "deliveryAccountableParty": "50616641",
        },
        sourcedocument_data={
            "objectIdAccountableParty": "test_upload",
            "name": "Test GMN",
            "deliveryContext": "waterwetPeilbeheer",
            "monitoringPurpose": "natuurbeheer",
            "groundwaterAspect": "kwaliteit",
            "startDateMonitoring": "2025-09-01",
        },
    )

    # 3. Since post_save signal should have fired,
    #    we check whether create_objects did its work.
    #    Here you should assert on the *real side effects* of create_objects.
    #    For example, if create_objects makes DB entries:
    assert GMN.objects.filter(bro_id="BRO123").exists()

    gmn_instance = GMN.objects.get(bro_id="BRO123")
    assert gmn_instance.internal_id == "test_upload"
    assert gmn_instance.name == "Test GMN"
    assert gmn_instance.delivery_context == "waterwetPeilbeheer"
    assert gmn_instance.monitoring_purpose == "natuurbeheer"
    assert gmn_instance.groundwater_aspect == "kwaliteit"


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_create_objects_frd(organisation: Organisation):  # noqa: F811
    """
    Test that saving an UploadTask with status COMPLETED calls create_objects.
    We don’t mock, so we directly check the side effects on the database.
    """
    # 2. Create a completed UploadTask
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="FRD",
        registration_type="FRD_StartRegistration",
        request_type="registration",
        status="COMPLETED",
        bro_id="BRO123",
        metadata={
            "qualityRegime": "IMBRO/A",
            "requestReference": "BROSTAR_Request",
            "deliveryAccountableParty": "50616641",
        },
        sourcedocument_data={
            "objectIdAccountableParty": "test_upload",
            "gmwBroId": "BRO123",
            "tubeNumber": 1,
            "linkedGmns": ["GMN00000123456"],
        },
    )

    # 3. Since post_save signal should have fired,
    #    we check whether create_objects did its work.
    #    Here you should assert on the *real side effects* of create_objects.
    #    For example, if create_objects makes DB entries:
    assert FRD.objects.filter(bro_id="BRO123").exists()

    frd_object = FRD.objects.get(bro_id="BRO123")
    assert frd_object.internal_id == "test_upload"


GMW_EVENT_TYPES = [
    "GMW_Positions",
    "GMW_PositionsMeasuring",
    "GMW_WellHeadProtector",
    "GMW_Owner",
    "GMW_Shift",
    "GMW_GroundLevel",
    "GMW_GroundLevelMeasuring",
    "GMW_Insertion",
    "GMW_TubeStatus",
    "GMW_Lengthening",
    "GMW_Shortening",
    "GMW_ElectrodeStatus",
    "GMW_Maintainer",
    "GMW_Removal",
]


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_create_objects_gmw_event(
    organisation: Organisation,  # noqa: F811
    gmw: GMW,  # noqa: F811
):
    """
    Test that saving an UploadTask with status COMPLETED calls create_objects.
    We don’t mock, so we directly check the side effects on the database.
    """
    # 2. Create a completed UploadTask
    for event in GMW_EVENT_TYPES:
        UploadTask.objects.create(
            data_owner=organisation,
            bro_domain="GMW",
            registration_type=event,
            request_type="registration",
            status="COMPLETED",
            bro_id=gmw.bro_id,
            metadata={
                "qualityRegime": "IMBRO/A",
                "requestReference": "BROSTAR_Request",
                "deliveryAccountableParty": "50616641",
            },
            sourcedocument_data={
                "objectIdAccountableParty": "test_upload",
                "eventDate": "2025-09-10",
                "gmwBroId": "BRO123",
                "tubeNumber": 1,
                "linkedGmns": ["GMN00000123456"],
            },
        )

        # 3. Since post_save signal should have fired,
        #    we check whether create_objects did its work.
        #    Here you should assert on the *real side effects* of create_objects.
        #    For example, if create_objects makes DB entries:
        assert GMW.objects.filter(bro_id=gmw.bro_id).exists()
        if event == "GMW_Removal":
            gmw = GMW.objects.get(bro_id=gmw.bro_id)
            assert gmw.removed == "ja"

        assert Event.objects.filter(gmw=gmw, event_name=event).exists()


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_pdok(
    organisation: Organisation,  # noqa: F811
    gmw: GMW,  # noqa: F811
):
    """
    Test that saving an UploadTask with status COMPLETED calls create_objects.
    We don’t mock, so we directly check the side effects on the database.
    """
    # 2. Create a completed UploadTask
    for event in ["GMW_Shortening", "GMW_Lengthening"]:
        task = UploadTask.objects.create(
            data_owner=organisation,
            bro_domain="GMW",
            registration_type=event,
            request_type="registration",
            status="PROCESSING",
            bro_id=gmw.bro_id,
            metadata={
                "qualityRegime": "IMBRO/A",
                "requestReference": "BROSTAR_Request",
                "deliveryAccountableParty": "50616641",
                "broId": "GMW000000082831",
            },
            sourcedocument_data={
                "eventDate": "2025-09-10",
                "monitoringTubes": [
                    {
                        "tubeNumber": 1,
                        "tubeTopPosition": "12.5",
                        "plainTubePartLength": None,
                    }
                ],
                "linkedGmns": ["GMN00000123456"],
            },
        )

    task.refresh_from_db()
    assert (
        task.sourcedocument_data["monitoringTubes"][0]["plainTubePartLength"]
        is not None
    )


GMN_EVENT_TYPES = [
    "GMN_MeasuringPoint",
    "GMN_TubeReference",
    "GMN_MeasuringPointEndDate",
]


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_create_objects_gmn_event(
    organisation: Organisation,  # noqa: F811
    gmn: GMN,  # noqa: F811
):
    """
    Test that saving an UploadTask with status COMPLETED calls create_objects.
    We don’t mock, so we directly check the side effects on the database.
    """
    # 2. Create a completed UploadTask
    event_dates = ["2024-09-10", "2024-10-10", "2024-11-10"]
    for event, event_date in zip(GMN_EVENT_TYPES, event_dates):
        UploadTask.objects.create(
            data_owner=organisation,
            bro_domain="GMN",
            registration_type=event,
            request_type="registration",
            status="COMPLETED",
            bro_id=gmn.bro_id,
            metadata={
                "qualityRegime": "IMBRO/A",
                "requestReference": "BROSTAR_Request",
                "deliveryAccountableParty": "50616641",
            },
            sourcedocument_data={
                "objectIdAccountableParty": "test_upload",
                "eventDate": event_date,
                "measuringPointCode": "MP1",
                "broId": "GMW000000034567"
                if event == "GMN_MeasuringPoint"
                else "GMW000000012345",
                "tubeNumber": 1,
            },
        )

        # 3. Since post_save signal should have fired,
        #    we check whether create_objects did its work.
        #    Here you should assert on the *real side effects* of create_objects.
        #    For example, if create_objects makes DB entries:
        assert GMN.objects.filter(bro_id=gmn.bro_id).exists()
        assert Measuringpoint.objects.filter(gmn=gmn, event_type=event).exists()

        if event == "GMN_MeasuringPointEndDate":
            measuringpoint = Measuringpoint.objects.get(
                gmn=gmn, measuringpoint_code="MP1", event_type="GMN_MeasuringPoint"
            )
            assert measuringpoint.measuringpoint_end_date.isoformat() == "2024-11-10"
            assert measuringpoint.measuringpoint_start_date.isoformat() == "2024-09-10"
            assert measuringpoint.tube_end_date.isoformat() == "2024-10-10"

            measuringpoint = Measuringpoint.objects.get(
                gmn=gmn, measuringpoint_code="MP1", event_type="GMN_TubeReference"
            )
            assert measuringpoint.measuringpoint_end_date.isoformat() == "2024-11-10"
            assert measuringpoint.measuringpoint_start_date.isoformat() == "2024-09-10"
            assert measuringpoint.tube_end_date.isoformat() == "2024-11-10"

        elif event == "GMN_TubeReference":
            measuringpoint = Measuringpoint.objects.get(
                gmn=gmn, measuringpoint_code="MP1", event_type="GMN_MeasuringPoint"
            )
            assert measuringpoint.tube_end_date.isoformat() == "2024-10-10"


@pytest.mark.django_db
def test_pre_save_uploadtask_triggers_insert(
    organisation: Organisation,  # noqa: F811
    gmw: GMW,  # noqa: F811
):
    task = UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMW",
        registration_type="GMW_WellHeadProtector",
        request_type="registration",
        status="FAILED",
        bro_id=gmw.bro_id,
        metadata={
            "qualityRegime": "IMBRO/A",
            "requestReference": "BROSTAR_Request",
            "deliveryAccountableParty": "50616641",
        },
        sourcedocument_data={
            "objectIdAccountableParty": "test_upload",
            "eventDate": "2025-09-10",
            "gmwBroId": "BRO123",
            "tubeNumber": 1,
            "linkedGmns": ["GMN00000123456"],
        },
        bro_errors="Op 2025-01 gebeurtenis mag niet voor de laatst geregistreerde gebeurtenis 2025-02 liggen.",
    )

    assert task.request_type == "insert"
    assert task.bro_errors == ""
    assert task.status == "PROCESSING"
    assert task.metadata.get("correctionReason") == "eigenCorrectie"

    # test list input

    task.request_type = "registration"
    task.bro_errors = [
        "Op 2025-01 gebeurtenis mag niet voor de laatst geregistreerde gebeurtenis 2025-02 liggen."
    ]
    task.save()

    assert task.request_type == "insert"
    assert task.bro_errors == ""
    assert task.status == "PROCESSING"


# ── Update tests ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_update_objects_gmw(
    organisation: Organisation,  # noqa: F811
    gmw: GMW,  # noqa: F811
):
    """Saving a replace UploadTask for GMW_Construction updates GMW fields and upserts MonitoringTubes."""
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMW",
        registration_type="GMW_Construction",
        request_type="replace",
        status="COMPLETED",
        bro_id=gmw.bro_id,
        metadata={
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "99999999",
        },
        sourcedocument_data={
            "nitgCode": "B09A0001",
            "owner": "11111111",
            "deliveredLocation": "250000 450000",
            "objectIdAccountableParty": "updated_id",
            "monitoringTubes": [
                {
                    "tubeNumber": 1,
                    "tubeType": "standaardbuis",
                    "tubeStatus": "gebruiksklaar",
                    "tubeMaterial": "pvc",
                    "tubeTopPosition": "1.0",
                    "plainTubePartLength": "2.0",
                    "screenLength": "1.0",
                    "sedimentSumpPresent": "nee",
                    "artesianWellCapPresent": "nee",
                    "variableDiameter": "nee",
                    "numberOfGeoOhmCables": 0,
                    "geoOhmCables": [],
                }
            ],
        },
    )

    gmw.refresh_from_db()
    assert gmw.nitg_code == "B09A0001"
    assert gmw.owner == "11111111"
    assert gmw.quality_regime == "IMBRO"
    assert gmw.internal_id == "updated_id"
    assert gmw.standardized_location is not None

    assert MonitoringTube.objects.filter(gmw=gmw, tube_number=1).exists()
    tube_obj = MonitoringTube.objects.get(gmw=gmw, tube_number=1)
    assert tube_obj.tube_material == "pvc"


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_update_objects_gmw_event(
    organisation: Organisation,  # noqa: F811
    gmw: GMW,  # noqa: F811
):
    """Replacing a GMW event updates its metadata and sourcedocument_data."""
    Event.objects.create(
        gmw=gmw,
        event_name="GMW_Positions",
        event_date="2025-01-10",
        data_owner=organisation,
        metadata={"qualityRegime": "IMBRO/A"},
        sourcedocument_data={"eventDate": "2025-01-10"},
    )

    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMW",
        registration_type="GMW_Positions",
        request_type="replace",
        status="COMPLETED",
        bro_id=gmw.bro_id,
        metadata={"qualityRegime": "IMBRO", "deliveryAccountableParty": "88888888"},
        sourcedocument_data={
            "eventDate": "2025-01-10",
            "wellHeadProtector": "kokerPlastic",
        },
    )

    event = Event.objects.get(gmw=gmw, event_name="GMW_Positions")
    assert event.metadata["qualityRegime"] == "IMBRO"
    assert event.sourcedocument_data["wellHeadProtector"] == "kokerPlastic"


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_update_objects_gmw_event_move(
    organisation: Organisation,  # noqa: F811
    gmw: GMW,  # noqa: F811
):
    """Moving a GMW event (dateToBeCorrected) updates its event_date."""
    Event.objects.create(
        gmw=gmw,
        event_name="GMW_Owner",
        event_date="2025-01-10",
        data_owner=organisation,
        metadata={"qualityRegime": "IMBRO/A"},
        sourcedocument_data={"eventDate": "2025-01-10"},
    )

    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMW",
        registration_type="GMW_Owner",
        request_type="move",
        status="COMPLETED",
        bro_id=gmw.bro_id,
        metadata={"qualityRegime": "IMBRO/A"},
        sourcedocument_data={
            "dateToBeCorrected": "2025-01-10",
            "eventDate": "2025-03-01",
        },
    )

    event = Event.objects.get(gmw=gmw, event_name="GMW_Owner")
    assert str(event.event_date) == "2025-03-01"


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_update_objects_gmw_removal(
    organisation: Organisation,  # noqa: F811
    gmw: GMW,  # noqa: F811
):
    """Replacing a GMW_Removal event updates its metadata and sourcedocument_data."""
    Event.objects.create(
        gmw=gmw,
        event_name="GMW_Removal",
        event_date="2025-06-01",
        data_owner=organisation,
        metadata={"qualityRegime": "IMBRO/A"},
        sourcedocument_data={"eventDate": "2025-06-01", "removalReason": "old"},
    )

    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMW",
        registration_type="GMW_Removal",
        request_type="replace",
        status="COMPLETED",
        bro_id=gmw.bro_id,
        metadata={"qualityRegime": "IMBRO"},
        sourcedocument_data={"eventDate": "2025-06-01", "removalReason": "updated"},
    )

    event = Event.objects.get(gmw=gmw, event_name="GMW_Removal")
    assert event.sourcedocument_data["removalReason"] == "updated"
    assert event.metadata["qualityRegime"] == "IMBRO"


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_update_objects_gld(
    organisation: Organisation,  # noqa: F811
    gld: GLD,  # noqa: F811
):
    """Replacing a GLD_StartRegistration updates GLD fields."""
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GLD",
        registration_type="GLD_StartRegistration",
        request_type="replace",
        status="COMPLETED",
        bro_id=gld.bro_id,
        metadata={
            "qualityRegime": "IMBRO",
            "deliveryAccountableParty": "77777777",
        },
        sourcedocument_data={
            "objectIdAccountableParty": "updated_gld_id",
            "gmwBroId": "GMW999999999",
            "tubeNumber": 3,
        },
    )

    gld.refresh_from_db()
    assert gld.internal_id == "updated_gld_id"
    assert gld.gmw_bro_id == "GMW999999999"
    assert str(gld.tube_number) == "3"
    assert gld.quality_regime == "IMBRO"
    assert gld.delivery_accountable_party == "77777777"


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_update_objects_gld_observation(
    organisation: Organisation,  # noqa: F811
    gld: GLD,  # noqa: F811
    observation,  # noqa: F811
):
    """Replacing a GLD_Addition updates the matching Observation fields."""
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GLD",
        registration_type="GLD_Addition",
        request_type="replace",
        status="COMPLETED",
        bro_id=gld.bro_id,
        metadata={"qualityRegime": "IMBRO"},
        sourcedocument_data={
            "dateToBeCorrected": "2024-01-01",
            "beginPosition": "2024-01-01",
            "endPosition": "2024-12-31",
            "observationType": "controlemeting",
            "investigatorKvk": "99999999",
            "processReference": "updatedProcess",
            "evaluationProcedure": "updatedProcedure",
            "measurementInstrumentType": "elektronischPeilklokje",
        },
    )

    observation.refresh_from_db()
    assert observation.observation_type == "controlemeting"
    assert observation.investigator_kvk == "99999999"
    assert observation.process_reference == "updatedProcess"


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_update_objects_gmn(
    organisation: Organisation,  # noqa: F811
    gmn: GMN,  # noqa: F811
):
    """Replacing a GMN_StartRegistration updates GMN fields."""
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMN",
        registration_type="GMN_StartRegistration",
        request_type="replace",
        status="COMPLETED",
        bro_id=gmn.bro_id,
        metadata={"qualityRegime": "IMBRO"},
        sourcedocument_data={
            "name": "Updated GMN name",
            "monitoringPurpose": "strategischBeheerKwaliteitRegionaal",
            "groundwaterAspect": "kwantiteit",
            "deliveryContext": "waterwetPeilbeheer",
            "startDateMonitoring": "2025-01-01",
        },
    )

    gmn.refresh_from_db()
    assert gmn.name == "Updated GMN name"
    assert gmn.monitoring_purpose == "strategischBeheerKwaliteitRegionaal"
    assert gmn.groundwater_aspect == "kwantiteit"
    assert gmn.quality_regime == "IMBRO"


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_update_objects_gmn_measuringpoint(
    organisation: Organisation,  # noqa: F811
    gmn: GMN,  # noqa: F811
    measuringpoint,  # noqa: F811
):
    """Replacing a GMN_MeasuringPoint updates the matching Measuringpoint fields."""
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMN",
        registration_type="GMN_MeasuringPoint",
        request_type="replace",
        status="COMPLETED",
        bro_id=gmn.bro_id,
        metadata={"qualityRegime": "IMBRO/A"},
        sourcedocument_data={
            "measuringPointCode": "MP123456",
            "broId": "GMW999999999",
            "tubeNumber": 2,
            "eventDate": "2025-06-01",
        },
    )

    measuringpoint.refresh_from_db()
    assert measuringpoint.gmw_bro_id == "GMW999999999"
    assert str(measuringpoint.tube_number) == "2"


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_update_objects_frd(
    organisation: Organisation,  # noqa: F811
    frd,  # noqa: F811
):
    """Replacing a FRD_StartRegistration updates FRD fields."""
    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="FRD",
        registration_type="FRD_StartRegistration",
        request_type="replace",
        status="COMPLETED",
        bro_id=frd.bro_id,
        metadata={"qualityRegime": "IMBRO"},
        sourcedocument_data={
            "objectIdAccountableParty": "updated_frd_id",
            "gmwBroId": "GMW888888888",
            "tubeNumber": 4,
            "deliveryAccountableParty": "55555555",
        },
    )

    frd.refresh_from_db()
    assert frd.internal_id == "updated_frd_id"
    assert frd.gmw_bro_id == "GMW888888888"
    assert str(frd.tube_number) == "4"
    assert frd.quality_regime == "IMBRO"
    assert frd.delivery_accountable_party == "55555555"


# ── Delete tests ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_delete_objects_gld_closure(
    organisation: Organisation,  # noqa: F811
    gld: GLD,  # noqa: F811
    observation,  # noqa: F811
):
    """A delete UploadTask for GLD_Closure removes the matching Observation."""
    assert Observation.objects.filter(gld=gld).count() == 1

    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GLD",
        registration_type="GLD_Closure",
        request_type="delete",
        status="COMPLETED",
        bro_id=gld.bro_id,
        metadata={},
        sourcedocument_data={"dateToBeCorrected": "2024-01-01"},
    )

    assert Observation.objects.filter(gld=gld).count() == 0


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_delete_objects_gmn_closure(
    organisation: Organisation,  # noqa: F811
    gmn: GMN,  # noqa: F811
    intermediate_event,  # noqa: F811
):
    """A delete UploadTask for GMN_Closure removes the matching IntermediateEvent."""
    assert IntermediateEvent.objects.filter(gmn=gmn).count() == 1

    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="GMN",
        registration_type="GMN_Closure",
        request_type="delete",
        status="COMPLETED",
        bro_id=gmn.bro_id,
        metadata={},
        sourcedocument_data={"dateToBeCorrected": "2024-01-01"},
    )

    assert IntermediateEvent.objects.filter(gmn=gmn).count() == 0


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_delete_objects_frd_gem_measurement_configuration(
    organisation: Organisation,  # noqa: F811
    frd,  # noqa: F811
    measurement_configuration,  # noqa: F811
):
    """A delete UploadTask for FRD_GEM_MeasurementConfiguration removes the matching MeasurementConfiguration."""
    assert MeasurementConfiguration.objects.filter(frd=frd).count() == 1

    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="FRD",
        registration_type="FRD_GEM_MeasurementConfiguration",
        request_type="delete",
        status="COMPLETED",
        bro_id=frd.bro_id,
        metadata={},
        sourcedocument_data={"measurementConfigurationId": "MC001"},
    )

    assert MeasurementConfiguration.objects.filter(frd=frd).count() == 0


@pytest.mark.django_db
def test_post_save_uploadtask_triggers_delete_objects_frd_gem_measurement(
    organisation: Organisation,  # noqa: F811
    frd,  # noqa: F811
    geo_electric_measurement,  # noqa: F811
):
    """A delete UploadTask for FRD_GEM_Measurement removes the matching GeoElectricMeasurement."""
    assert GeoElectricMeasurement.objects.filter(frd=frd).count() == 1

    UploadTask.objects.create(
        data_owner=organisation,
        bro_domain="FRD",
        registration_type="FRD_GEM_Measurement",
        request_type="delete",
        status="COMPLETED",
        bro_id=frd.bro_id,
        metadata={},
        sourcedocument_data={"dateToBeCorrected": "2024-01-01"},
    )

    assert GeoElectricMeasurement.objects.filter(frd=frd).count() == 0
