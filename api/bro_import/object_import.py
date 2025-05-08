import datetime
import logging
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import IO, Any

import polars as pl
import requests
import requests.adapters
import xmltodict
from django.conf import settings
from requests.auth import HTTPBasicAuth

from api.models import Organisation
from frd.models import FRD
from gar.models import GAR
from gld.models import GLD, Observation
from gmn.choices import GMN_EVENT_MAPPING
from gmn.models import GMN, IntermediateEvent, Measuringpoint
from gmw.models import GMW, Event, MonitoringTube

logger = logging.getLogger("general")


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

    bro_domain: str

    def __init__(self, bro_id: str, data_owner: Organisation) -> None:
        if not bro_id.startswith(self.bro_domain):
            raise ValueError(f"Incorrect BRO-ID for domain: {self.bro_domain}")

        self.bro_id = bro_id
        self.data_owner = data_owner

        self.s = requests.Session()
        auth = HTTPBasicAuth(
            username=data_owner.bro_user_token,
            password=data_owner.bro_user_password,
        )
        self.s.headers = {"Content-Type": "application/json"}
        self.s.auth = auth
        retry = requests.adapters.Retry(
            total=6,
            backoff_factor=0.5,
        )
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=5, pool_maxsize=5, max_retries=retry
        )
        self.s.mount("http://", adapter)
        self.s.mount("https://", adapter)

    def run(self) -> None:
        url = self._create_download_url()
        xml_data = self._download_xml(url)
        logger.info(f"Downloaded XML data for {self.bro_domain} with ID {self.bro_id}")
        json_data = self._convert_xml_to_json(xml_data)
        self._save_data_to_database(json_data)
        logger.info(f"Saved data for {self.bro_domain} with ID {self.bro_id}")

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
    bro_domain = "GMN"

    def _save_data_to_database(self, json_data: dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If GMN_PPO is not found, it basically means that the object is not relevant anymore
        if "GMN_PPO" not in dispatch_document_data:
            return

        gmn_data, measuringpoint_data, intermediate_events = self._split_json_data(
            dispatch_document_data
        )

        self._save_gmn_data(gmn_data)
        self._create_events_df(intermediate_events)
        self._save_measuringpoint_data(measuringpoint_data)

    def _create_events_df(self, events_data: list[dict, Any]) -> None:
        event_types = []
        event_dates = []
        measuring_point_codes = []
        for event in events_data:
            event_type = event.get("eventName", {}).get("#text", None)
            event_date = event.get("eventDate", {}).get("brocom:date", None)
            measuring_point_code = event.get("measuringPointCode", {})
            if not event_type or not event_date or not measuring_point_code:
                continue

            event_types.append(event_type)
            event_dates.append(event_date)
            measuring_point_codes.append(measuring_point_code)

        self.events_df = pl.DataFrame(
            data={
                "eventType": event_types,
                "eventDate": event_dates,
                "measuringPointCode": measuring_point_codes,
            }
        )

    def _split_json_data(
        self, dispatch_document_data: dict[str, Any]
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Takes in the json data and splits it up into GMN and Measuringpoint data"""

        intermediate_events = (
            dispatch_document_data["GMN_PPO"]
            .get("monitoringNetHistory", {})
            .get("intermediateEvent", [])
        )

        measuringpoint_data = dispatch_document_data["GMN_PPO"].get(
            "measuringPoint", []
        )

        # Whenever the GMN exists of 1 measuringpoint, it is a single object. We want a list
        if isinstance(measuringpoint_data, dict):
            measuringpoint_data = [measuringpoint_data]

        gmn_data = dispatch_document_data["GMN_PPO"]
        gmn_data.pop("measuringPoint", None)

        return gmn_data, measuringpoint_data, intermediate_events

    def _save_gmn_data(self, gmn_data: dict[str, Any]) -> None:
        self.gmn_obj = GMN.objects.update_or_create(
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
        )[0]

    def _save_measuringpoint_data(
        self, measuringpoint_data: list[dict[str, Any]]
    ) -> None:
        for measuringpoint in measuringpoint_data:
            mp_data = measuringpoint.get("MeasuringPoint", {})

            monitoring_tubes_data = mp_data.get("monitoringTube", {})

            # If a measuringpoint has old monitoringtube references, mp_data is a list
            # The last one is the active one, and therefore the one of interest
            if isinstance(monitoring_tubes_data, dict):
                monitoring_tubes_data = [monitoring_tubes_data]

            for monitoring_tube_reference in monitoring_tubes_data:
                monitoring_tube_data = monitoring_tube_reference.get(
                    "GroundwaterMonitoringTube", {}
                )
                bro_id = monitoring_tube_data.get("broId", None)
                tube_nr = monitoring_tube_data.get("tubeNumber", None)
                mp_start_date = mp_data.get("startDate", {}).get("brocom:date", None)
                mp_end_date = mp_data.get("endDate", {}).get("brocom:date", None)

                mp_code = mp_data.get("measuringPointCode", None)
                event_date = monitoring_tube_data.get("startDate", {}).get(
                    "brocom:date", None
                )
                end_date = mp_data.get("endDate", {}).get("brocom:date", None)

                event = self.events_df.filter(
                    pl.col("eventDate").eq(event_date)
                    & pl.col("measuringPointCode").eq(mp_code)
                )

                if not event.is_empty():
                    event_name = event.item(0, 0)
                    event_type = GMN_EVENT_MAPPING[event_name]
                    IntermediateEvent.objects.update_or_create(
                        gmn=self.gmn_obj,
                        data_owner=self.gmn_obj.data_owner,
                        measuringpoint_code=mp_code,
                        event_date=event_date,
                        event_type=event_type,
                        defaults={"gmw_bro_id": bro_id, "tube_number": tube_nr},
                    )
                else:
                    event_type = "GMN_StartRegistration"

                defaults = {
                    "measuringpoint_start_date": mp_start_date,
                    "measuringpoint_end_date": mp_end_date,
                    "tube_number": tube_nr,
                    "tube_start_date": event_date,
                    "tube_end_date": end_date,
                    "event_type": event_type,
                }

                Measuringpoint.objects.update_or_create(
                    gmn=self.gmn_obj,
                    data_owner=self.data_owner,
                    measuringpoint_code=mp_code,
                    gmw_bro_id=bro_id,
                    defaults=defaults,
                )


class GMWObjectImporter(ObjectImporter):
    bro_domain = "GMW"

    def retrieve_internal_id(
        self,
        bro_id: str,
    ) -> str:
        bronhouder_url = settings.BRONHOUDERSPORTAAL_URL
        try:
            r = self.s.get(
                url=f"{bronhouder_url}/api/v2/transacties/?zoekveld=broId&zoektekst={bro_id}",
                timeout=15,
            )
        except Exception as e:
            logger.exception(e)
            return None

        transacties = r.json().get("transacties", None)
        if transacties is None:
            return None

        bronhouder_data = pl.DataFrame(transacties)
        if bronhouder_data.is_empty():
            return None

        intern_ids = bronhouder_data.select("objectIdBronhouder")
        intern_id = intern_ids.item(-1, 0)
        return intern_id

    def _save_data_to_database(self, json_data: dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If GMW_PPO is not found, it basically means that the object is not relevant anymore
        if "GMW_PPO" not in dispatch_document_data:
            return

        gmw_data, monitoringtubes_data = self._split_json_data(dispatch_document_data)

        event_data = gmw_data.get("wellHistory", [])

        self._save_gmw_data(gmw_data)
        self._save_monitoringtubes_data(monitoringtubes_data, event_data)
        self._save_events_data(event_data)

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
        well_construction_date: dict = gmw_data.get("wellHistory", {}).get(
            "wellConstructionDate", {}
        )
        intern_id = self.retrieve_internal_id(gmw_data.get("brocom:broId", None))
        self.gmw_obj = GMW.objects.update_or_create(
            intern_id=intern_id,
            bro_id=gmw_data.get("brocom:broId", None),
            data_owner=self.data_owner,
            defaults={
                "delivery_accountable_party": gmw_data.get(
                    "brocom:deliveryAccountableParty", None
                ),
                "quality_regime": gmw_data.get("brocom:qualityRegime", None),
                "well_construction_date": well_construction_date.get("brocom:date")
                or well_construction_date.get("brocom:year"),
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
                "horizontal_positioning_method": gmw_data.get("deliveredLocation", {})
                .get("gmwcommon:horizontalPositioningMethod", {})
                .get("#text", None),
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
        )[0]

    def _save_monitoringtubes_data(
        self,
        monitoringtubes_data: list[dict[str, Any]] | dict[str, Any],
        event_data: list[dict[str, any]],
    ) -> None:
        # If only one monitoringtube data, the monitoringtubes_data is not in a list
        if not isinstance(monitoringtubes_data, list):
            monitoringtubes_data = [monitoringtubes_data]

        for monitoringtube in monitoringtubes_data:
            geo_ohm_data = []
            geo_ohm_cables = monitoringtube.get("geoOhmCable", [])

            # If geoOhmCable is not in a list, make it a list
            if not isinstance(geo_ohm_cables, list):
                geo_ohm_cables = [geo_ohm_cables]

            for cable in geo_ohm_cables:
                electrodes = cable.get("electrode", [])
                # If electrodes is not in a list, make it a list
                if not isinstance(electrodes, list):
                    electrodes = [electrodes]

                electrode_data = []
                for electrode in electrodes:
                    electrode_data.append(
                        {
                            "electrode_number": electrode.get(
                                "gmwcommon:electrodeNumber", None
                            ),
                            "electrode_packing_material": electrode.get(
                                "gmwcommon:electrodePackingMaterial", {}
                            ).get("#text", None),
                            "electrode_status": electrode.get(
                                "gmwcommon:electrodeStatus", {}
                            ).get("#text", None),
                            "electrode_position": electrode.get(
                                "gmwcommon:electrodePosition", {}
                            ).get("#text", None),
                        }
                    )

                geo_ohm_data.append(
                    {
                        "cable_number": cable.get("cableNumber", None),
                        "cable_in_use": cable.get("cableInUse", None),
                        "electrodes": electrode_data,
                    }
                )

            MonitoringTube.objects.update_or_create(
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
                    "sediment_sump_length": monitoringtube.get("sedimentSump", {})
                    .get("gmwcommon:sedimentSumpLength", {})
                    .get("#text")
                    if monitoringtube.get("sedimentSump", {}).get(
                        "gmwcommon:sedimentSumpLength"
                    )
                    else None,
                    "number_of_geo_ohm_cables": monitoringtube.get(
                        "numberOfGeoOhmCables", None
                    ),
                    "geo_ohm_cables": geo_ohm_data or [],
                    "tube_top_diameter": monitoringtube.get("tubeTopDiameter", {}).get(
                        "#text"
                    ),
                    "variable_diameter": monitoringtube.get("variableDiameter", None),
                    "tube_status": monitoringtube.get("tubeStatus", {}).get(
                        "#text", None
                    ),
                    "tube_top_position": self._lookup_most_recent_top_position(
                        monitoringtube, event_data
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

    def _get_well_data(self, intermediate_event: list[dict[str, any]]) -> dict:
        event_data = intermediate_event.get("eventData", {}).get("wellData", {})
        if not event_data:
            return {}

        well_data = {}
        for key in event_data.keys():
            if isinstance(event_data[key], str):
                well_data[key] = event_data[key]
            else:
                well_data[key] = event_data[key].get("#text", None)

        return well_data

    def _get_tube_data(self, intermediate_event: list[dict[str, any]]) -> list[dict]:
        event_data = intermediate_event.get("eventData", {}).get("tubeData", {})
        if not event_data:
            return {}

        tubes_data = []
        if isinstance(event_data, list):
            for tube in event_data:
                tube_data = {}
                for key in tube.keys():
                    if isinstance(tube[key], (str | int)):
                        tube_data[key] = tube[key]
                    else:
                        tube_data[key] = tube[key].get("#text", None)
                tubes_data.append(tube_data)

            return tube_data

        tube_data = {}
        for key in event_data.keys():
            if isinstance(event_data[key], (str | int)):
                tube_data[key] = event_data[key]
            else:
                tube_data[key] = event_data[key].get("#text", None)
        tubes_data.append(tube_data)
        return tubes_data

    def _save_events_data(self, event_data: list[dict[str, any]]):
        intermediate_events = event_data.get("intermediateEvent", [])
        if isinstance(intermediate_events, dict):
            intermediate_events = [intermediate_events]

        for intermediate_event in intermediate_events:
            name = intermediate_event.get("eventName", {}).get("#text")
            event_date = intermediate_event.get("eventDate", {}).get(
                "brocom:date"
            ) or intermediate_event.get("eventDate", {}).get("brocom:year")

            # If event_date is a year, convert it to a date
            if event_date:
                event_date = (
                    event_date + "-01-01" if len(event_date) == 4 else event_date
                )
            else:
                continue

            metadata = {
                "broId": self.gmw_obj.bro_id,
                "qualityRegime": self.gmw_obj.quality_regime,
                "deliveryAccountableParty": self.gmw_obj.delivery_accountable_party,
            }

            sourcedocument_data = self._get_well_data(intermediate_event)
            sourcedocument_data["monitoringTubes"] = self._get_tube_data(
                intermediate_event
            )

            Event.objects.update_or_create(
                gmw=self.gmw_obj,
                data_owner=self.data_owner,
                event_name=name,
                event_date=event_date,
                defaults={
                    "metadata": metadata,
                    "sourcedocument_data": sourcedocument_data,
                },
            )

    def _lookup_most_recent_top_position(
        self, monitoringtube: list[dict[str, any]], event_data: list[dict[str, any]]
    ):
        """In the BRO uigifteservice, the most recent top position is not always found in the metadata.
        Instead, the eventdata has to be checked for any changes.
        This function checks if the most recent value is found in the event history.
        If not, the initial value is returned."""

        initial_top_position = monitoringtube.get("tubeTopPosition", {}).get("#text")
        tube_number = monitoringtube.get("tubeNumber")
        most_recent_date = None
        most_recent_position = None

        intermediate_events = event_data.get("intermediateEvent", [])
        if isinstance(intermediate_events, dict):
            intermediate_events = [intermediate_events]

        for intermediate_event in intermediate_events:
            if (
                intermediate_event.get("eventName", {}).get("#text")
                == "nieuweInmetingPosities"
            ):
                event_date = intermediate_event.get("eventDate", {}).get(
                    "brocom:date"
                ) or intermediate_event.get("eventDate", {}).get("brocom:year")

                # If event_date is a year, convert it to a date
                if event_date:
                    event_date = (
                        event_date + "-01-01" if len(event_date) == 4 else event_date
                    )
                else:
                    continue
                tube_data = intermediate_event.get("eventData", {}).get("tubeData")

                # Ensure tube_data is a list
                if isinstance(tube_data, dict):
                    tube_data = [tube_data]

                for tube in tube_data:
                    if tube.get("tubeNumber") == tube_number:
                        if most_recent_date is None or event_date > most_recent_date:
                            most_recent_date = event_date
                            most_recent_position = tube.get("tubeTopPosition", {}).get(
                                "#text"
                            )

        return most_recent_position or initial_top_position


class GARObjectImporter(ObjectImporter):
    bro_domain = "GAR"

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

        GAR.objects.update_or_create(
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


OBSERVATION_NAMESPACE = {
    "gco": "http://www.isotc211.org/2005/gco",
    "swe": "http://www.opengis.net/swe/2.0",
    "xlink": "http://www.w3.org/1999/xlink",
    "gldcommon": "http://www.broservices.nl/xsd/gldcommon/1.0",
    "brocom": "http://www.broservices.nl/xsd/brocommon/3.0",
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gml": "http://www.opengis.net/gml/3.2",
    "om": "http://www.opengis.net/om/2.0",
    "waterml": "http://www.opengis.net/waterml/2.0",
    "": "http://www.broservices.nl/xsd/dsgld/1.0",  # Default namespace (empty prefix)
}


def date_or_none(string: str | None) -> datetime.date:
    """DD-MM-YYYY to Datetime.Date"""
    if string:
        return datetime.datetime.strptime(string, "%d-%m-%Y").date()


class GLDObjectImporter(ObjectImporter):
    bro_domain = "GLD"

    def _create_download_url(self) -> str:
        """Creates the import url for a given bro object."""
        bro_domain = self.bro_domain.lower()
        url = f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/{bro_domain}/v1/objects/{self.bro_id}?fullHistory=nee&observationPeriodBeginDate=2021-01-01&observationPeriodEndDate=2021-01-01"

        return url

    def _save_data_to_database(self, json_data: dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If GLD_O  is not found, it basically means that the object is not relevant anymore
        if "GLD_O" not in dispatch_document_data:
            return

        gld_data = dispatch_document_data.get("GLD_O")
        monitoring_point_data = gld_data.get("monitoringPoint").get(
            "gldcommon:GroundwaterMonitoringTube"
        )

        gmn_ids = self._gmn_ids(gld_data)

        self.gld = GLD.objects.update_or_create(
            bro_id=gld_data.get("brocom:broId", None),
            data_owner=self.data_owner,
            defaults={
                "delivery_accountable_party": gld_data.get(
                    "brocom:deliveryAccountableParty", None
                ),
                "quality_regime": gld_data.get("brocom:qualityRegime", None),
                "gmw_bro_id": monitoring_point_data.get("gldcommon:broId", None),
                "tube_number": monitoring_point_data.get("gldcommon:tubeNumber", None),
                "research_first_date": gld_data.get("researchFirstDate", None),
                "research_last_date": gld_data.get("researchLastDate", None),
                "linked_gmns": gmn_ids,
            },
        )[0]
        self._save_observations()

    def _gmn_ids(self, gld_data: dict[list[dict[str, any]]]) -> list:
        """Retrieve a list of all coupled gmn-ids."""
        # Navigate to the `groundwaterMonitoringNet` key
        monitoring_nets = gld_data.get("groundwaterMonitoringNet", {})
        gmn_ids = []
        if isinstance(monitoring_nets, dict):
            monitoring_nets = [monitoring_nets]

        for monitoring_net in monitoring_nets:
            bro_id = monitoring_net.get("gldcommon:broId")
            if bro_id:
                gmn_ids.append(bro_id)

        return gmn_ids

    def _observation_summary(self):
        url = f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/gld/v1/objects/{self.bro_id}/observationsSummary"
        r = requests.get(url=url)
        r.raise_for_status()
        return r.json()

    def _procedure_information(self, observation_id: str):
        url = f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/gld/v1/objects/{self.bro_id}/observations/{observation_id}?startTVPTime=1900-01-01T00%3A00%3A00&endTVPTime=1900-01-01T00%3A00%3A00"
        r = requests.get(url=url)
        r.raise_for_status()
        return ET.fromstring(r.content)

    def _format_procedure(self, observation: ET.Element) -> dict:
        procedure = {}

        named_values = observation.findall(".//om:NamedValue", OBSERVATION_NAMESPACE)
        for named_value in named_values:
            name = (
                named_value.find(".//om:name", OBSERVATION_NAMESPACE)
                .attrib.get("{http://www.w3.org/1999/xlink}href", "None:None")
                .split(":")[-1]
            )
            if name == "principalInvestigator":
                value = named_value.find(".//om:value", OBSERVATION_NAMESPACE)
                procedure.update(
                    {
                        "InvestigatorKvk": value.find(
                            ".//gldcommon:chamberOfCommerceNumber",
                            OBSERVATION_NAMESPACE,
                        ).text
                    }
                )
            else:
                value = named_value.find(".//om:value", OBSERVATION_NAMESPACE).text
                procedure.update({name: value})

        process_reference_element = observation.find(
            ".//waterml:processReference", OBSERVATION_NAMESPACE
        )
        if process_reference_element is not None:
            process_reference = process_reference_element.attrib.get(
                "{http://www.w3.org/1999/xlink}href", "None:None"
            ).split(":")[-1]
        else:
            process_reference = None

        procedure.update(
            {
                "ProcessReference": process_reference,
                "ResultTime": observation.find(
                    ".//om:resultTime", OBSERVATION_NAMESPACE
                )
                .find(".//gml:timePosition", OBSERVATION_NAMESPACE)
                .text,
            }
        )
        try:
            procedure.update(
                {
                    "InvestigatorKvk": observation.find(
                        ".//gldcommon:chamberOfCommerceNumber", OBSERVATION_NAMESPACE
                    ).text
                }
            )
        except AttributeError:
            logger.info("No chamberOfCommerceNumber found.")

        return procedure

    def _save_observations(self):
        observation_summary = self._observation_summary()
        for observation in observation_summary:
            observation_id = observation.get("observationId", None)
            if not observation_id:
                continue

            observation_tree = self._procedure_information(observation_id)
            observation_element = observation_tree.find(
                ".//observation", namespaces=OBSERVATION_NAMESPACE
            )
            procedure = self._format_procedure(observation_element)
            begin_position = date_or_none(observation.get("startDate", None))
            end_position = date_or_none(observation.get("endDate", None))

            observation = Observation.objects.update_or_create(
                gld=self.gld,
                data_owner=self.data_owner,
                observation_id=observation_id,
                defaults=(
                    {
                        "begin_position": begin_position,
                        "end_position": end_position,
                        "observation_type": observation.get("observationType", None),
                        "validation_status": observation.get("observationStatus", None),
                        "investigator_kvk": procedure.get("InvestigatorKvk", None),
                        "result_time": procedure.get("ResultTime", None),
                        "process_reference": procedure.get("ProcessReference", None),
                        "air_pressure_compensation_type": procedure.get(
                            "airPressureCompensationType", None
                        ),
                        "evaluation_procedure": procedure.get(
                            "evaluationProcedure", None
                        ),
                        "measurement_instrument_type": procedure.get(
                            "measurementInstrumentType", None
                        ),
                    }
                ),
            )[0]


class FRDObjectImporter(ObjectImporter):
    bro_domain = "FRD"

    def _save_data_to_database(self, json_data: dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If FRD_O  is not found, it basically means that the object is not relevant anymore
        if "FRD_O" not in dispatch_document_data:
            return

        frd_data = dispatch_document_data.get("FRD_O")
        tube_data = frd_data.get("groundwaterMonitoringTube").get(
            "frdcom:MonitoringTube"
        )

        FRD.objects.update_or_create(
            bro_id=frd_data.get("brocom:broId", None),
            data_owner=self.data_owner,
            defaults={
                "delivery_accountable_party": frd_data.get(
                    "brocom:deliveryAccountableParty", None
                ),
                "quality_regime": frd_data.get("brocom:qualityRegime", None),
                "gmw_bro_id": tube_data.get("frdcom:broId", None),
                "tube_number": tube_data.get("frdcom:tubeNumber", None),
                "research_first_date": frd_data.get("researchFirstDate", None),
                "research_last_date": frd_data.get("researchLastDate", None),
            },
        )
