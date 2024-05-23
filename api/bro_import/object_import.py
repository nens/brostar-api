from abc import ABC, abstractmethod
from typing import IO, Any

import requests
import xmltodict
from django.conf import settings

from gar.models import GAR
from gmn.models import GMN, Measuringpoint
from gmw.models import GMW, MonitoringTube


class ObjectImporter(ABC):
    """Imports the BRO data based on the object ID.

    Args:
        bro_domain (str): The BRO domain for the object.
        bro_id (str): The unique identifier of the BRO object.

    The run method should be called after initializing. It handles:

        1) Creation of URL
        2) Download of the XML
        3) Translation from XML to JSON
        4) Save actions into the database
    """

    def __init__(self, bro_domain: str, bro_id: str, data_owner: str) -> None:
        self.bro_domain = bro_domain
        self.bro_id = bro_id
        self.data_owner = data_owner

    def run(self) -> None:
        url = self._create_download_url()
        xml_data = self._download_xml(url)
        json_data = self._convert_xml_to_json(xml_data)
        self._save_data_to_database(json_data)

    def _create_download_url(self) -> str:
        """Creates the import url for a given bro object."""
        bro_domain = self.bro_domain.lower()
        url = f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/{bro_domain}/v1/objects/{self.bro_id}?fullHistory=nee"
        return url

    def _download_xml(self, url: str) -> IO[bytes]:
        """Downloads the BRO XML file based on an url"""
        r = requests.get(url=url)
        r.raise_for_status()

        return r.content

    def _convert_xml_to_json(self, xml_data: IO[bytes]) -> dict[str, Any]:
        json_data = xmltodict.parse(xml_data)

        return json_data

    @abstractmethod
    def _save_data_to_database(self, json_data: dict[str, Any]) -> None:
        """Saves the downloaded BRO data into the Django database."""
        pass


class GMNObjectImporter(ObjectImporter):
    def _save_data_to_database(self, json_data: dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If GMN_PPO is not found, it basically means that the object is not relevant anymore
        if "GMN_PPO" not in dispatch_document_data:
            return

        gmn_data, measuringpoint_data = self._split_json_data(dispatch_document_data)

        self._save_gmn_data(gmn_data)
        self._save_measuringpoint_data(measuringpoint_data)

    def _split_json_data(
        self, dispatch_document_data: dict[str, Any]
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Takes in the json data and splits it up into GMN and Measuringpoint data"""

        measuringpoint_data = dispatch_document_data["GMN_PPO"].get(
            "measuringPoint", []
        )

        # Whenever the GMN exists of 1 measuringpoint, it is a single object. We want a list
        if isinstance(measuringpoint_data, dict):
            measuringpoint_data = [measuringpoint_data]

        gmn_data = dispatch_document_data["GMN_PPO"]
        gmn_data.pop("measuringPoint", None)

        return gmn_data, measuringpoint_data

    def _save_gmn_data(self, gmn_data: dict[str, Any]) -> None:
        self.gmn_obj, created = GMN.objects.update_or_create(
            bro_id=gmn_data.get("brocom:broId", None),
            data_owner=self.data_owner,
            defaults={
                "delivery_accountable_party": gmn_data.get(
                    "brocom:deliveryAccountableParty", None
                ),
                "quality_regime": gmn_data.get("brocom:qualityRegime", None),
                "name": gmn_data.get("name", None),
                "delivery_context": gmn_data.get("deliveryContext", {}).get(
                    "#text", None
                ),
                "monitoring_purpose": gmn_data.get("monitoringPurpose", {}).get(
                    "#text", None
                ),
                "groundwater_aspect": gmn_data.get("groundwaterAspect", {}).get(
                    "#text", None
                ),
                "start_date_monitoring": gmn_data.get("monitoringNetHistory", {})
                .get("startDateMonitoring", {})
                .get("brocom:date", None),
                "object_registration_time": gmn_data.get("registrationHistory", {}).get(
                    "brocom:objectRegistrationTime", None
                ),
                "registration_status": gmn_data.get("registrationHistory", {})
                .get("brocom:registrationStatus", {})
                .get("#text", None),
            },
        )

        self.gmn_obj.save()

    def _save_measuringpoint_data(
        self, measuringpoint_data: list[dict[str, Any]]
    ) -> None:
        for measuringpoint in measuringpoint_data:
            mp_data = measuringpoint.get("MeasuringPoint", {})
            monitoring_tube_data = mp_data.get("monitoringTube", {}).get(
                "GroundwaterMonitoringTube", {}
            )

            measuringpoint_obj, created = Measuringpoint.objects.update_or_create(
                gmn=self.gmn_obj,
                data_owner=self.data_owner,
                measuringpoint_code=mp_data.get("measuringPointCode", None),
                defaults={
                    "measuringpoint_start_date": mp_data.get("startDate", {}).get(
                        "brocom:date", None
                    ),
                    "gmw_bro_id": monitoring_tube_data.get("broId", None),
                    "tube_number": monitoring_tube_data.get("tubeNumber", None),
                    "tube_start_date": monitoring_tube_data.get("startDate", None).get(
                        "brocom:date", None
                    ),
                },
            )

            measuringpoint_obj.save()


class GMWObjectImporter(ObjectImporter):
    def _save_data_to_database(self, json_data: dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If GMW_PPO is not found, it basically means that the object is not relevant anymore
        if "GMW_PPO" not in dispatch_document_data:
            return

        gmw_data, monitoringtubes_data = self._split_json_data(dispatch_document_data)

        self._save_gmw_data(gmw_data)
        self._save_monitoringtubes_data(monitoringtubes_data)

    def _split_json_data(
        self, dispatch_document_data: dict[str, Any]
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Takes in the json data and splits it up into GMW and tubes data"""

        monitoringtubes_data = dispatch_document_data["GMW_PPO"].get(
            "monitoringTube", []
        )

        gmw_data = dispatch_document_data["GMW_PPO"]
        gmw_data.pop("monitoringTube", None)

        return gmw_data, monitoringtubes_data

    def _save_gmw_data(self, gmw_data: dict[str, Any]) -> None:
        self.gmw_obj, created = GMW.objects.update_or_create(
            bro_id=gmw_data.get("brocom:broId", None),
            data_owner=self.data_owner,
            defaults={
                "delivery_accountable_party": gmw_data.get(
                    "brocom:deliveryAccountableParty", None
                ),
                "quality_regime": gmw_data.get("brocom:qualityRegime", None),
                "delivery_context": gmw_data.get("deliveryContext", {}).get(
                    "#text", None
                ),
                "construction_standard": gmw_data.get("constructionStandard", {}).get(
                    "#text", None
                ),
                "initial_function": gmw_data.get("initialFunction", {}).get(
                    "#text", None
                ),
                "removed": gmw_data.get("removed", None),
                "ground_level_stable": gmw_data.get("groundLevelStable", None),
                "well_stability": gmw_data.get("wellStability", {}).get("#text", None),
                "nitg_code": gmw_data.get("nitgCode", None),
                "well_code": gmw_data.get("wellCode", None),
                "owner": gmw_data.get("owner", None),
                "well_head_protector": gmw_data.get("wellHeadProtector", {}).get(
                    "#text", None
                ),
                "delivered_location": gmw_data.get("deliveredLocation", {})
                .get("gmwcommon:location", {})
                .get("gml:pos", None),
                "local_vertical_reference_point": gmw_data.get(
                    "deliveredVerticalPosition", {}
                )
                .get("gmwcommon:localVerticalReferencePoint", {})
                .get("#text", None),
                "offset": gmw_data.get("deliveredVerticalPosition", {})
                .get("gmwcommon:offset", {})
                .get("#text", None),
                "vertical_datum": gmw_data.get("deliveredVerticalPosition", {})
                .get("gmwcommon:verticalDatum", {})
                .get("#text", None),
                "ground_level_position": gmw_data.get("deliveredVerticalPosition", {})
                .get("gmwcommon:groundLevelPosition", {})
                .get("#text", None),
                "ground_level_positioning_method": gmw_data.get(
                    "deliveredVerticalPosition", {}
                )
                .get("gmwcommon:groundLevelPositioningMethod", {})
                .get("#text", None),
                "standardized_location": gmw_data.get("standardizedLocation", {})
                .get("brocom:location", {})
                .get("gml:pos", None),
                "object_registration_time": gmw_data.get("registrationHistory", {}).get(
                    "brocom:objectRegistrationTime", None
                ),
                "registration_status": gmw_data.get("registrationHistory", {})
                .get("brocom:registrationStatus", {})
                .get("#text", None),
            },
        )

        self.gmw_obj.save()

    def _save_monitoringtubes_data(
        self, monitoringtubes_data: list[dict[str, Any]]
    ) -> None:
        # If only one monitoringtube data, the monitoringtubes_data is not in a list
        if not isinstance(monitoringtubes_data, list):
            monitoringtubes_data = [monitoringtubes_data]

        for monitoringtube in monitoringtubes_data:
            monitoringtube_obj, created = MonitoringTube.objects.update_or_create(
                gmw=self.gmw_obj,
                data_owner=self.data_owner,
                tube_number=monitoringtube.get("tubeNumber", None),
                defaults={
                    "tube_type": monitoringtube.get("tubeType", {}).get("#text", None),
                    "artesian_well_cap_present": monitoringtube.get(
                        "artesianWellCapPresent", None
                    ),
                    "sediment_sump_present": monitoringtube.get(
                        "sedimentSumpPresent", None
                    ),
                    "number_of_geo_ohm_cables": monitoringtube.get(
                        "numberOfGeoOhmCables", None
                    ),
                    "tube_top_diameter": monitoringtube.get("tubeTopDiameter", {}).get(
                        "@xsi:nil", None
                    ),
                    "variable_diameter": monitoringtube.get("variableDiameter", None),
                    "tube_status": monitoringtube.get("tubeStatus", {}).get(
                        "#text", None
                    ),
                    "tube_top_position": monitoringtube.get("tubeTopPosition", {}).get(
                        "#text", None
                    ),
                    "tube_top_positioning_method": monitoringtube.get(
                        "tubeTopPositioningMethod", {}
                    ).get("#text", None),
                    "tube_part_inserted": monitoringtube.get("tubePartInserted", None),
                    "tube_in_use": monitoringtube.get("tubeInUse", None),
                    "tube_packing_material": monitoringtube.get("materialUsed", {})
                    .get("gmwcommon:tubePackingMaterial", {})
                    .get("#text", None),
                    "tube_material": monitoringtube.get("materialUsed", {})
                    .get("gmwcommon:tubeMaterial", {})
                    .get("#text", None),
                    "glue": monitoringtube.get("materialUsed", {})
                    .get("gmwcommon:glue", {})
                    .get("#text", None),
                    "screen_length": monitoringtube.get("screen", {})
                    .get("screenLength", {})
                    .get("#text", None),
                    "sock_material": monitoringtube.get("screen", {})
                    .get("sockMaterial", {})
                    .get("#text", None),
                    "screen_top_position": monitoringtube.get("screen", {})
                    .get("screenTopPosition", {})
                    .get("#text", None),
                    "screen_bottom_position": monitoringtube.get("screen", {})
                    .get("screenBottomPosition", {})
                    .get("#text", None),
                    "plain_tube_part_length": monitoringtube.get("plainTubePart", {})
                    .get("gmwcommon:plainTubePartLength", {})
                    .get("#text", None),
                },
            )

            monitoringtube_obj.save()


class GARObjectImporter(ObjectImporter):
    def _save_data_to_database(self, json_data: dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If GAR_O  is not found, it basically means that the object is not relevant anymore
        if "GAR_O" not in dispatch_document_data:
            return

        gar_data = dispatch_document_data.get("GAR_O")
        monitoring_point_data = gar_data.get("monitoringPoint", None).get(
            "garcommon:GroundwaterMonitoringTube", None
        )
        field_research_data = gar_data.get("fieldResearch", None)
        field_observation_data = field_research_data.get(
            "garcommon:fieldObservation", None
        )
        lab_analysis = gar_data.get("laboratoryAnalysis", None)

        if lab_analysis:
            analysis_process = lab_analysis.get("garcommon:analysisProcess", None)
            if isinstance(analysis_process, list):
                lab_analysis_date = (
                    lab_analysis.get("garcommon:analysisProcess", None)[0]
                    .get("garcommon:analysisDate", None)
                    .get("brocom:date")
                )
            else:
                lab_analysis_date = (
                    lab_analysis.get("garcommon:analysisProcess", None)
                    .get("garcommon:analysisDate", None)
                    .get("brocom:date")
                )
        else:
            lab_analysis_date = None

        self.gar_obj, created = GAR.objects.update_or_create(
            bro_id=gar_data.get("brocom:broId", None),
            data_owner=self.data_owner,
            defaults={
                "delivery_accountable_party": gar_data.get(
                    "brocom:deliveryAccountableParty", None
                ),
                "quality_regime": gar_data.get("brocom:qualityRegime", None),
                "quality_control_method": gar_data.get(
                    "qualityControlMethod", None
                ).get("#text", None),
                "gmw_bro_id": monitoring_point_data.get("garcommon:broId", None),
                "tube_number": monitoring_point_data.get("garcommon:tubeNumber", None),
                "sampling_datetime": field_research_data.get(
                    "garcommon:samplingDateTime", None
                ),
                "sampling_standard": field_research_data.get(
                    "garcommon:samplingStandard", None
                ).get("#text", None),
                "pump_type": field_research_data.get("garcommon:samplingDevice", None)
                .get("garcommon:pumpType", None)
                .get("#text", None),
                "abnormality_in_cooling": field_observation_data.get(
                    "garcommon:abnormalityInCooling", None
                ),
                "abnormality_in_device": field_observation_data.get(
                    "garcommon:abnormalityInDevice", None
                ),
                "polluted_by_engine": field_observation_data.get(
                    "garcommon:pollutedByEngine", None
                ),
                "filter_aerated": field_observation_data.get(
                    "garcommon:filterAerated", None
                ),
                "groundwater_level_dropped_too_much": field_observation_data.get(
                    "garcommon:groundWaterLevelDroppedTooMuch", None
                ),
                "abnormal_filter": field_observation_data.get(
                    "garcommon:abnormalFilter", None
                ),
                "sample_aerated": field_observation_data.get(
                    "garcommon:sampleAerated", None
                ),
                "hose_reused": field_observation_data.get("garcommon:hoseReused", None),
                "temperature_difficult_to_measure": field_observation_data.get(
                    "garcommon:temperatureDifficultToMeasure", None
                ),
                "lab_analysis_date": lab_analysis_date,
            },
        )

        self.gar_obj.save()
