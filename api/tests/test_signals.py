# tests/test_signals.py
import pytest

from api.models import UploadTask
from api.tests.fixtures import gmw, organisation  # noqa: F401
from frd.models import FRD
from gld.models import GLD  # Example model to check side effects
from gmn.models import GMN
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

    gld = GLD.objects.get(bro_id="GLD000000012345")
    assert gld.internal_id == "test_upload"
    assert gld.bro_id == "GLD000000012345"
    assert gld.gmw_bro_id == "BRO123"
    assert int(gld.tube_number) == 1


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

    gmn = GMN.objects.get(bro_id="BRO123")
    assert gmn.internal_id == "test_upload"
    assert gmn.name == "Test GMN"
    assert gmn.delivery_context == "waterwetPeilbeheer"
    assert gmn.monitoring_purpose == "natuurbeheer"
    assert gmn.groundwater_aspect == "kwaliteit"


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

    frd = FRD.objects.get(bro_id="BRO123")
    assert frd.internal_id == "test_upload"


EVENT_TYPES = [
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
    for event in EVENT_TYPES:
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
        assert Event.objects.filter(gmw=gmw, event_name=event).exists()


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
