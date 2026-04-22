import datetime
import logging
import time
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import IO, Any

import polars as pl
import requests
import xmltodict
from django.conf import settings
from requests.adapters import HTTPAdapter, Retry
from requests.auth import HTTPBasicAuth

from api.models import ImportTask, Organisation
from frd.models import (
    FRD,
    CalculatedApparentFormationResistance,
    GeoElectricMeasure,
    GeoElectricMeasurement,
    MeasurementConfiguration,
)
from gar.models import (
    GAR,
    Analysis,
    AnalysisProcess,
    FieldMeasurement,
    LaboratoryResearch,
)
from gld.models import GLD, Observation
from gmn.choices import GMN_EVENT_MAPPING
from gmn.models import GMN, IntermediateEvent, Measuringpoint
from gmw.models import GMW, Event, MonitoringTube
from gpd.models import GPD, Report, VolumeSeries
from guf.models import (
    GUF,
    DesignInstallation,
    DesignWell,
    EnergyCharacteristics,
    GUFEvent,
)

logger = logging.getLogger("general")


def check_dates(
    last_import_date: datetime.datetime,
    last_correction_date: str | None,
    last_addition_date: str | None,
    registration_completion_time: str | None,
) -> bool:
    """Check if any of the date fields is more recent than the last_import_date"""
    dates = [
        datetime.datetime.fromisoformat(d)
        for d in [
            last_correction_date,
            last_addition_date,
            registration_completion_time,
        ]
        if d is not None
    ]

    if not dates:
        return True  # No update dates available, default to importing

    return max(dates) > last_import_date


DOMAIN_MODEL_MAPPING = {
    "GMN": GMN,
    "GMW": GMW,
    "GAR": GAR,
    "GLD": GLD,
    "FRD": FRD,
    "GPD": GPD,
}


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
    bro_category: str = "gm"

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
        retry = Retry(
            total=6,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(pool_connections=5, pool_maxsize=5, max_retries=retry)
        self.s.mount("http://", adapter)
        self.s.mount("https://", adapter)

    def should_import(self) -> bool:
        """Check PDOK API to see if the last_correction_date or the last_addition_date is more recent than the last_import_date"""
        last_import_task = (
            ImportTask.objects.filter(
                data_owner=self.data_owner,
                bro_domain=self.bro_domain,
                created__lt=datetime.datetime.now() - datetime.timedelta(days=1),
            )
            .order_by("-created")
            .first()
        )
        logger.info(
            f"Last import task for {self.bro_domain} and ID {self.bro_id}: {last_import_task}"
        )
        last_import_date = last_import_task.created if last_import_task else None
        if last_import_date is None:
            logger.info(
                f"No previous import found for {self.bro_domain} and ID {self.bro_id} - Should import"
            )
            return True  # No previous import, so we should import

        model = DOMAIN_MODEL_MAPPING.get(self.bro_domain)
        if not model or not model.objects.filter(bro_id=self.bro_id).exists():
            logger.info(
                f"No existing object found in DB for {self.bro_domain} and ID {self.bro_id} - Should import"
            )
            return True  # Object not in database, so we should import

        try:
            r = self.s.get(
                f"https://api.pdok.nl/bzk/bro-gminsamenhang-karakteristieken/ogc/v1/collections/gm_{self.bro_domain.lower()}/items?f=jsonfg&bro_id={self.bro_id}"
            )
            r.raise_for_status()

            data = r.json().get("features", [])

            if len(data) != 1:
                logger.info(
                    f"No data found in PDOK for {self.bro_domain} and ID {self.bro_id} - Should import"
                )
                return True  # If no data found, default to importing

            properties = data[0].get("properties", {})
            last_correction_date = properties.get(
                "latest_correction_time", None
            )  # ISO String or None e.g. 2025-11-10T15:33:26+01:00
            last_addition_date = properties.get(
                "latest_addition_time", None
            )  # ISO String or None
            registration_completion_time = properties.get(
                "registration_completion_time", None
            )  # ISO String or None

            if check_dates(
                last_import_date,
                last_correction_date,
                last_addition_date,
                registration_completion_time,
            ):
                logger.info(
                    f"Data is more recent in PDOK for {self.bro_domain} and ID {self.bro_id} - Should import - dates: {last_correction_date}, {last_addition_date}, {registration_completion_time}"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Error checking PDOK for bro_id {self.bro_id}: {e}")
            return True  # Default to importing if there's an error

    def run(self, force: bool = False) -> None:
        if not self.should_import() and not force:
            logger.info(f"No import needed for {self.bro_domain} with ID {self.bro_id}")
            return

        url = self._create_download_url()
        xml_data = self._download_xml(url)
        logger.info(f"Downloaded XML data for {self.bro_domain} with ID {self.bro_id}")
        json_data = self._convert_xml_to_json(xml_data)
        self._save_data_to_database(json_data)
        logger.info(f"Saved data for {self.bro_domain} with ID {self.bro_id}")

    def _create_download_url(self) -> str:
        """Creates the import url for a given bro object."""
        bro_domain = self.bro_domain.lower()
        bro_category = self.bro_category.lower()
        url = f"{settings.BRO_UITGIFTE_SERVICE_URL}/{bro_category}/{bro_domain}/v1/objects/{self.bro_id}?fullHistory=nee"
        return url

    def _download_xml(self, url: str) -> IO[bytes]:
        """Downloads the BRO XML file based on an url"""
        r = self.s.get(url=url)
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

    def _create_events_df(self, events_data: list[dict, Any] | dict[str, Any]) -> None:
        event_types = []
        event_dates = []
        measuring_point_codes = []
        if isinstance(events_data, dict):
            events_data = [events_data]

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
        if isinstance(measuringpoint_data, dict):
            measuringpoint_data = [measuringpoint_data]

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
    ) -> str | None:
        bronhouder_url = settings.BRONHOUDERSPORTAAL_URL
        try:
            r = self.s.get(
                url=f"{bronhouder_url}/api/v2/transacties/?zoekveld=broId&zoektekst={bro_id}",
                timeout=15,
            )
            # Check if the request was successful
            r.raise_for_status()

            # Check if response has content
            if not r.content or len(r.content.strip()) == 0:
                logger.info(f"Empty response for bro_id: {bro_id}")
                return None

        except Exception as e:
            logger.info(f"Error fetching internal ID for bro_id {bro_id}: {e}")
            return None

        transacties = r.json().get("transacties", None)
        if transacties is None:
            return None

        bronhouder_data = pl.DataFrame(transacties)
        if (
            bronhouder_data.is_empty()
            or "objectIdBronhouder" not in bronhouder_data.columns
        ):
            return None

        internal_ids = bronhouder_data.select("objectIdBronhouder")
        internal_id = internal_ids.item(-1, 0)
        return internal_id

    def _save_data_to_database(self, json_data: dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If GMW_PPO is not found, it basically means that the object is not relevant anymore
        if "GMW_PPO" not in dispatch_document_data:
            logger.warning(
                "GMW_PPO not found in dispatch document data, no data to save."
            )
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
        internal_id = self.retrieve_internal_id(gmw_data.get("brocom:broId", ""))
        self.gmw_obj = GMW.objects.update_or_create(
            bro_id=gmw_data.get("brocom:broId", None),
            data_owner=self.data_owner,
            defaults={
                "internal_id": internal_id[:100]
                if internal_id
                else None,  # Only accepts 100 chars
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

        gar, _ = GAR.objects.update_or_create(
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

        self._save_field_measurements(gar, field_research_data)
        if lab_analysis:
            self._save_laboratory_researches(gar, lab_analysis)

    @staticmethod
    def _attr_or_none(value: Any, attr: str) -> str | None:
        """Return an attribute value from a xmltodict dict, or None."""
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get(f"@{attr}", None)
        return None

    @staticmethod
    def _text_or_none(value: Any) -> str | None:
        """Return the #text value from a xmltodict dict, or the plain string, or None."""
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get("#text", None)
        return value

    def _save_field_measurements(
        self, gar: GAR, field_research_data: dict[str, Any]
    ) -> None:
        raw = field_research_data.get("garcommon:fieldMeasurement", None)
        if not raw:
            return

        measurements = raw if isinstance(raw, list) else [raw]

        FieldMeasurement.objects.filter(gar=gar).delete()
        for measurement in measurements:
            measurement_value = measurement.get(
                "garcommon:analysisMeasurementValue", None
            )

            FieldMeasurement.objects.create(
                gar=gar,
                parameter=int(measurement.get("garcommon:parameter")),
                unit=self._attr_or_none(measurement_value, "uom"),
                field_measurement_value=self._text_or_none(measurement_value),
                quality_control_status=self._text_or_none(
                    measurement.get("garcommon:qualityControlStatus", None)
                ),
            )

    def _save_laboratory_researches(
        self, gar: GAR, lab_analysis_data: dict | list
    ) -> None:
        lab_analyses = (
            lab_analysis_data
            if isinstance(lab_analysis_data, list)
            else [lab_analysis_data]
        )

        LaboratoryResearch.objects.filter(gar=gar).delete()
        for lab_analysis in lab_analyses:
            responsible_lab = lab_analysis.get("garcommon:responsibleLaboratory", None)
            kvk_number = None
            if responsible_lab:
                kvk_number = self._text_or_none(
                    responsible_lab.get("garcommon:chamberOfCommerceNumber", None)
                )

            lab_research = LaboratoryResearch.objects.create(
                gar=gar,
                laboratory_kvk_number=kvk_number,
            )
            self._save_analysis_processes(lab_research, lab_analysis)

    def _save_analysis_processes(
        self, lab_research: LaboratoryResearch, lab_analysis_data: dict[str, Any]
    ) -> None:
        raw = lab_analysis_data.get("garcommon:analysisProcess", None)
        if not raw:
            return

        processes = raw if isinstance(raw, list) else [raw]

        for process in processes:
            analyses_date = process.get("garcommon:analysisDate", {}).get(
                "brocom:date", None
            )
            analysis_process = AnalysisProcess.objects.create(
                laboratory_research=lab_research,
                analyses_date=analyses_date,
                analytical_technique=self._text_or_none(
                    process.get("garcommon:analyticalTechnique", None)
                ),
                validation_method=self._text_or_none(
                    process.get("garcommon:valuationMethod", None)
                ),
            )
            self._save_analyses(analysis_process, process)

    def _save_analyses(
        self, analysis_process: AnalysisProcess, process_data: dict[str, Any]
    ) -> None:
        raw = process_data.get("garcommon:analysis", None)
        if not raw:
            return

        analyses = raw if isinstance(raw, list) else [raw]

        for analysis in analyses:
            analysis_value = analysis.get("garcommon:analysisMeasurementValue", None)
            Analysis.objects.create(
                analysis_process=analysis_process,
                parameter=int(analysis.get("garcommon:parameter")),
                value=self._text_or_none(analysis_value),
                unit=self._attr_or_none(analysis_value, "uom"),
                limit_symbol=self._text_or_none(
                    analysis.get("garcommon:limitSymbol", None)
                ),
                reporting_limit=self._text_or_none(
                    analysis.get("garcommon:reportingLimit", None)
                ),
                status_quality_control=self._text_or_none(
                    analysis.get("garcommon:qualityControlStatus", None)
                ),
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

    def _observation_summary(self) -> list[dict[str, Any]]:
        url = f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/gld/v1/objects/{self.bro_id}/observationsSummary"
        r = self.s.get(url=url)

        if r.status_code == 429:
            wait_time = int(r.headers.get("Retry-After", 5))
            logger.info(
                f"Received 429 Too Many Requests. Retrying after {wait_time} seconds."
            )
            time.sleep(wait_time)
            return self._observation_summary()

        r.raise_for_status()

        return r.json()

    def _procedure_information(self, observation_id: str):
        url = f"{settings.BRO_UITGIFTE_SERVICE_URL}/gm/gld/v1/objects/{self.bro_id}/observations/{observation_id}?startTVPTime=1900-01-01T00%3A00%3A00&endTVPTime=1900-01-01T00%3A00%3A00"
        r = self.s.get(url=url)

        if r.status_code == 429:
            wait_time = int(r.headers.get("Retry-After", 5))
            logger.info(
                f"Received 429 Too Many Requests. Retrying after {wait_time} seconds."
            )
            time.sleep(wait_time)
            return self._procedure_information(observation_id)

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
                # This write measurementInstrumentType, evaluationProcedure and airPressureCompensationType to the procedure dict
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
        if isinstance(observation_summary, dict):
            observation_summary = [observation_summary]

        for observation in observation_summary:
            time.sleep(0.5)  # To prevent hitting rate limits
            observation_id = observation.get("observationId", None)
            if not observation_id:
                continue

            observation_tree = self._procedure_information(observation_id)
            observation_element = observation_tree.find(
                ".//observation", namespaces=OBSERVATION_NAMESPACE
            )
            if observation_element is None:
                logger.info(
                    f"No observation element found for observation ID {observation_id}"
                )
                continue

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
            "frdcommon:MonitoringTube"
        )

        frd, _ = FRD.objects.update_or_create(
            bro_id=frd_data.get("brocom:broId", None),
            data_owner=self.data_owner,
            defaults={
                "delivery_accountable_party": frd_data.get(
                    "brocom:deliveryAccountableParty", None
                ),
                "quality_regime": frd_data.get("brocom:qualityRegime", None),
                "determination_type": frd_data.get("determinationType", {}).get(
                    "#text", None
                ),
                "gmw_bro_id": tube_data.get("frdcommon:broId", None),
                "tube_number": tube_data.get("frdcommon:tubeNumber", None),
                "research_first_date": frd_data.get("researchFirstDate", None),
                "research_last_date": frd_data.get("researchLastDate", None),
            },
        )

        self._save_measurement_configurations(frd, frd_data)
        self._save_geo_electric_measurements(frd, frd_data)

    @staticmethod
    def _text_or_none(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, dict):
            return value.get("#text", None)
        return value

    def _save_measurement_configurations(
        self, frd: FRD, frd_data: dict[str, Any]
    ) -> None:
        raw = frd_data.get("measurementConfiguration", None)
        if not raw:
            return
        configs = raw if isinstance(raw, list) else [raw]

        MeasurementConfiguration.objects.filter(frd=frd).delete()
        for config in configs:
            mc = config.get("frdcommon:MeasurementConfiguration", {})
            MeasurementConfiguration.objects.create(
                frd=frd,
                measurement_configuration_id=mc.get(
                    "frdcommon:measurementConfigurationID"
                ),
                measurement_pair=mc.get("frdcommon:measurementPair", None),
                current_pair=mc.get("frdcommon:currentPair", None),
            )

    def _save_geo_electric_measurements(
        self, frd: FRD, frd_data: dict[str, Any]
    ) -> None:
        raw = frd_data.get("relatedGeoElectricMeasurement", None)
        if not raw:
            return
        measurements = raw if isinstance(raw, list) else [raw]

        GeoElectricMeasurement.objects.filter(frd=frd).delete()
        for item in measurements:
            gem_data = item.get("frdcommon:GeoElectricMeasurement", {})
            gem = GeoElectricMeasurement.objects.create(
                frd=frd,
                measurement_date=gem_data.get("frdcommon:measurementDate", None),
                determination_procedure=self._text_or_none(
                    gem_data.get("frdcommon:determinationProcedure", None)
                ),
                evaluation_procedure=self._text_or_none(
                    gem_data.get("frdcommon:evaluationProcedure", None)
                ),
            )
            self._save_geo_electric_measures(gem, gem_data)
            self._save_calculated_resistance(gem, gem_data)

    def _save_geo_electric_measures(
        self, gem: GeoElectricMeasurement, gem_data: dict[str, Any]
    ) -> None:
        raw = gem_data.get("frdcommon:measure", None)
        if not raw:
            return
        measures = raw if isinstance(raw, list) else [raw]

        for measure in measures:
            GeoElectricMeasure.objects.create(
                geo_electric_measurement=gem,
                resistance=self._text_or_none(
                    measure.get("frdcommon:resistance", None)
                ),
                related_measurement_configuration=measure.get(
                    "frdcommon:relatedMeasurementConfiguration", {}
                ).get("@xlink:href", None),
            )

    def _save_calculated_resistance(
        self, gem: GeoElectricMeasurement, gem_data: dict[str, Any]
    ) -> None:
        raw = gem_data.get(
            "frdcommon:relatedCalculatedApparentFormationResistance", None
        )
        if not raw:
            return
        calc_data = raw.get("frdcommon:CalculatedApparentFormationResistance", {})
        values = (
            calc_data.get("frdcommon:apparentFormationResistanceSeries", {})
            .get("swe:DataArray", {})
            .get("swe:values", None)
        )
        CalculatedApparentFormationResistance.objects.create(
            geo_electric_measurement=gem,
            evaluation_procedure=self._text_or_none(
                calc_data.get("frdcommon:evaluationProcedure", None)
            ),
            values=values,
        )


class GUFObjectImporter(ObjectImporter):
    bro_domain = "GUF"
    bro_category = "gu"

    def _save_data_to_database(self, json_data: dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If GUF_PPO is not found, it basically means that the object is not relevant anymore
        if "GUF_PPO" not in dispatch_document_data:
            return

        guf_ppo = dispatch_document_data.get("GUF_PPO", {})

        # Create/update main GUF object
        guf_obj = self._save_guf_data(guf_ppo)

        # Process events from objectHistory
        self._save_guf_events(guf_ppo, guf_obj)

        # Process licence and nested installations/wells
        self._save_installations_and_wells(guf_ppo, guf_obj)

    def _parse_flexible_date(self, date_str: str | None) -> datetime.date | None:
        """Parse BRO dates with flexible granularity (YYYY, YYYY-MM, YYYY-MM-DD)"""
        if not date_str:
            return None
        try:
            if len(date_str) == 4:  # YYYY
                return datetime.date(int(date_str), 1, 1)
            elif len(date_str) == 7:  # YYYY-MM
                year, month = date_str.split("-")
                return datetime.date(int(year), int(month), 1)
            else:  # YYYY-MM-DD
                return datetime.datetime.fromisoformat(date_str).date()
        except (ValueError, AttributeError):
            return None

    def _extract_text_from_xml_element(self, element: dict | str | None) -> str | None:
        """Extract text from XML elements that may have attributes"""
        if isinstance(element, dict):
            return element.get("#text")
        return element

    def _save_guf_data(self, guf_ppo: dict[str, Any]):  # noqa C901 - This function is complex but breaking it down further would reduce readability due to the nested structure of the data.
        # Extract basic metadata
        bro_id = guf_ppo.get("brocom:broId")
        delivery_accountable_party = guf_ppo.get("brocom:deliveryAccountableParty")
        quality_regime = self._extract_text_from_xml_element(
            guf_ppo.get("brocom:qualityRegime")
        )
        delivery_context = self._extract_text_from_xml_element(
            guf_ppo.get("deliveryContext")
        )

        # Extract lifespan with flexible date handling
        lifespan = guf_ppo.get("lifespan", {})
        start_time_data = lifespan.get("gufcommon:startTime", {})
        start_time_str = None
        if start_time_data.get("brocom:date"):
            start_time_str = start_time_data.get("brocom:date")
        elif start_time_data.get("brocom:yearMonth"):
            start_time_str = start_time_data.get("brocom:yearMonth")
        elif start_time_data.get("brocom:year"):
            start_time_str = start_time_data.get("brocom:year")

        # Extract licence data for GUF fields.
        # The XML may contain multiple <licence> elements, which xmltodict parses as a list.
        # Use the first licence entry for GUF-level fields.
        licence_raw = guf_ppo.get("licence", {})
        if isinstance(licence_raw, list):
            licence_raw = licence_raw[0]
        licence_data = licence_raw.get("gufcommon:LicenceGroundwaterUsage", {})
        identification_licence = licence_data.get("gufcommon:identificationLicence")
        legal_type = self._extract_text_from_xml_element(
            licence_data.get("gufcommon:legalType")
        )

        # Extract usage type information
        usage_facility = licence_data.get("gufcommon:usageTypeFacility", {})
        primary_usage_type = self._extract_text_from_xml_element(
            usage_facility.get("gufcommon:primaryUsageType")
        )
        human_consumption = self._extract_text_from_xml_element(
            usage_facility.get("gufcommon:humanConsumption")
        )

        # Extract secondary usage types (array)
        secondary_types = usage_facility.get("gufcommon:secondaryUsageType", [])
        if isinstance(secondary_types, dict):
            secondary_types = [secondary_types]
        secondary_usage_types = [
            self._extract_text_from_xml_element(st) for st in secondary_types if st
        ]

        # Extract licensed quantities (array with units)
        licensed_quantities = []
        license_quantities_raw = licence_data.get("gufcommon:licensedQuantity", [])
        if isinstance(license_quantities_raw, dict):
            license_quantities_raw = [license_quantities_raw]

        for qty in license_quantities_raw:
            qty_obj = {
                "licensed_in_out": self._extract_text_from_xml_element(
                    qty.get("gufcommon:licensedInOut")
                ),
            }
            # Handle quantities with units
            for period in ["Hour", "Day", "Month", "Quarter", "Year"]:
                key = f"gufcommon:maximumPer{period}"
                if qty.get(key):
                    value_data = qty.get(key)
                    if isinstance(value_data, dict):
                        qty_obj[f"maximum_per_{period.lower()}"] = {
                            "value": value_data.get("#text"),
                            "unit": value_data.get("@uom", "m3"),
                        }
                    else:
                        qty_obj[f"maximum_per_{period.lower()}"] = {
                            "value": value_data,
                            "unit": "m3",
                        }
            licensed_quantities.append(qty_obj)

        # Create or update GUF object
        guf_obj, _ = GUF.objects.update_or_create(
            bro_id=bro_id,
            data_owner=self.data_owner,
            defaults={
                "delivery_accountable_party": delivery_accountable_party,
                "quality_regime": quality_regime,
                "delivery_context": delivery_context,
                "start_time": self._parse_flexible_date(start_time_str),
                "identification_licence": identification_licence,
                "legal_type": legal_type,
                "primary_usage_type": primary_usage_type,
                "human_consumption": human_consumption,
                "secondary_usage_types": secondary_usage_types,
                "licensed_quantities": licensed_quantities,
            },
        )

        return guf_obj

    def _save_guf_events(self, guf_ppo: dict[str, Any], guf_obj: GUF) -> None:
        # Extract events from objectHistory
        object_history = guf_ppo.get("objectHistory", {})
        events = object_history.get("event", [])
        if isinstance(events, dict):
            events = [events]

        for event_data in events:
            event_name = self._extract_text_from_xml_element(event_data.get("name"))
            event_date_str = event_data.get("date", {}).get("brocom:date")
            event_date = self._parse_flexible_date(event_date_str)

            if not event_name or not event_date:
                continue

            # Metadata for the event
            metadata = {
                "broId": guf_obj.bro_id,
                "qualityRegime": guf_obj.quality_regime,
                "deliveryAccountableParty": guf_obj.delivery_accountable_party,
            }

            # Sourcedocument data (entire event structure)
            sourcedocument_data = event_data.get("sourceDocument", {})

            GUFEvent.objects.update_or_create(
                guf=guf_obj,
                event_name=event_name,
                event_date=event_date,
                data_owner=self.data_owner,
                defaults={
                    "metadata": metadata,
                    "sourcedocument_data": sourcedocument_data,
                },
            )

    def _save_installations_and_wells(
        self, guf_ppo: dict[str, Any], guf_obj: GUF
    ) -> None:
        # The XML may contain multiple <licence> elements; xmltodict parses these as a list.
        # Iterate all licences so every DesignInstallation is captured.
        licence_raw = guf_ppo.get("licence", {})
        if isinstance(licence_raw, dict):
            licence_raw = [licence_raw]

        for licence_entry in licence_raw:
            licence_data = licence_entry.get("gufcommon:LicenceGroundwaterUsage", {})
            installations = licence_data.get("gufcommon:designInstallation", [])
            if isinstance(installations, dict):
                installations = [installations]

            for installation_data in installations:
                installation_obj = installation_data.get(
                    "gufcommon:DesignInstallation", {}
                )

                # Extract installation data
                design_installation_id = installation_obj.get(
                    "gufcommon:designInstallationId"
                )
                installation_function = self._extract_text_from_xml_element(
                    installation_obj.get("gufcommon:installationFunction")
                )

                # Extract geometry (Point coordinates)
                geometry = installation_obj.get("gufcommon:geometry", {})
                point = geometry.get("gml:Point", {})
                pos = point.get("gml:pos")

                # Create/update Installation
                installation_model, _ = DesignInstallation.objects.update_or_create(
                    guf=guf_obj,
                    design_installation_id=design_installation_id,
                    data_owner=self.data_owner,
                    defaults={
                        "installation_function": installation_function,
                        "design_installation_pos": pos,
                    },
                )

                # Process energy characteristics for this installation
                self._save_energy_characteristics(installation_obj, installation_model)

                # Process wells for this installation
                self._save_wells_for_installation(installation_obj, installation_model)

    def _save_energy_characteristics(
        self, installation_obj: dict[str, Any], installation_model
    ) -> None:
        """Import gufcommon:energyCharacteristics nested inside a DesignInstallation."""
        ec_data = installation_obj.get("gufcommon:energyCharacteristics")
        if not ec_data:
            return

        def _val(key: str) -> str | None:
            """Extract the text value from an element that may carry unit attributes."""
            raw = ec_data.get(key)
            if raw is None:
                return None
            if isinstance(raw, dict):
                return raw.get("#text")
            return str(raw)

        EnergyCharacteristics.objects.update_or_create(
            installation=installation_model,
            defaults={
                "data_owner": self.data_owner,
                "energy_cold": _val("gufcommon:energyCold"),
                "energy_warm": _val("gufcommon:energyWarm"),
                "maximum_infiltration_temperature_warm": _val(
                    "gufcommon:maximumInfiltrationTemperatureWarm"
                ),
                "average_infiltration_temperature_cold": _val(
                    "gufcommon:averageInfiltrationTemperatureCold"
                ),
                "average_infiltration_temperature_warm": _val(
                    "gufcommon:averageInfiltrationTemperatureWarm"
                ),
                "power_cold": _val("gufcommon:powerCold"),
                "power_warm": _val("gufcommon:powerWarm"),
                "power": _val("gufcommon:power"),
                "average_warm_water": _val("gufcommon:averageWarmWater"),
                "average_cold_water": _val("gufcommon:averageColdWater"),
                "maximum_year_quantity_warm": _val("gufcommon:maximumYearQuantityWarm"),
                "maximum_year_quantity_cold": _val("gufcommon:maximumYearQuantityCold"),
            },
        )

    def _save_wells_for_installation(
        self, installation_obj: dict[str, Any], installation_model
    ) -> None:
        # Extract wells
        wells = installation_obj.get("gufcommon:designWell", [])
        if isinstance(wells, dict):
            wells = [wells]

        for well_data in wells:
            well_obj = well_data.get("gufcommon:DesignWell", {})

            design_well_id = well_obj.get("gufcommon:designWellId")
            height_data = well_obj.get("gufcommon:height")
            height = (
                height_data.get("#text")
                if isinstance(height_data, dict)
                else height_data
            )

            # Extract well functions (can be multiple)
            well_functions_raw = well_obj.get("gufcommon:wellFunction", [])
            if isinstance(well_functions_raw, dict):
                well_functions_raw = [well_functions_raw]
            well_functions = [
                self._extract_text_from_xml_element(wf)
                for wf in well_functions_raw
                if wf
            ]

            # Extract boolean fields
            geometry_publicly_available = self._extract_text_from_xml_element(
                well_obj.get("gufcommon:geometryPubliclyAvailable")
            )
            max_well_depth_publicly_available = self._extract_text_from_xml_element(
                well_obj.get("gufcommon:maximumWellDepthPubliclyAvailable")
            )

            # Extract well geometry (Point coordinates)
            well_geometry = well_obj.get("gufcommon:geometry", {})
            well_point = well_geometry.get("gml:Point", {})
            well_pos = well_point.get("gml:pos")

            # Extract maximum well depth with unit
            max_well_depth_data = well_obj.get("gufcommon:maximumWellDepth")
            max_well_depth = (
                max_well_depth_data.get("#text")
                if isinstance(max_well_depth_data, dict)
                else max_well_depth_data
            )

            # Extract capacity with unit
            capacity_data = well_obj.get("gufcommon:maximumWellCapacity")
            capacity = (
                capacity_data.get("#text")
                if isinstance(capacity_data, dict)
                else capacity_data
            )

            # Extract relative temperature
            relative_temperature = self._extract_text_from_xml_element(
                well_obj.get("gufcommon:relativeTemperature")
            )

            # Extract design screen (nested object)
            design_screen_raw = well_obj.get("gufcommon:designScreen", {})
            design_screen = {}
            if design_screen_raw:
                screen_type_data = design_screen_raw.get("gufcommon:screenType")
                screen_top_data = design_screen_raw.get("gufcommon:designScreenTop")
                screen_bottom_data = design_screen_raw.get(
                    "gufcommon:designScreenBottom"
                )
                design_screen = {
                    "screen_type": self._extract_text_from_xml_element(
                        screen_type_data
                    ),
                    "design_screen_top": (
                        screen_top_data.get("#text")
                        if isinstance(screen_top_data, dict)
                        else screen_top_data
                    ),
                    "design_screen_bottom": (
                        screen_bottom_data.get("#text")
                        if isinstance(screen_bottom_data, dict)
                        else screen_bottom_data
                    ),
                }

            DesignWell.objects.update_or_create(
                installation=installation_model,
                design_well_id=design_well_id,
                data_owner=self.data_owner,
                defaults={
                    "height": height,
                    "well_functions": well_functions,
                    "well_pos": well_pos,
                    "geometry_publicly_available": geometry_publicly_available,
                    "maximum_well_depth": max_well_depth,
                    "maximum_well_depth_publicly_available": max_well_depth_publicly_available,
                    "maximum_well_capacity": capacity,
                    "relative_temperature": relative_temperature,
                    "design_screen": design_screen,
                },
            )


class GPDObjectImporter(ObjectImporter):
    bro_domain = "GPD"
    bro_category = "gu"

    def _save_data_to_database(self, json_data: dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If GPD_O is not found, it basically means that the object is not relevant anymore
        if "GPD_O" not in dispatch_document_data:
            return

        gpd_data = dispatch_document_data.get("GPD_O")

        # Parse lifespan
        lifespan = gpd_data.get("lifespan", {})
        start_time = lifespan.get("startTime")
        end_time = lifespan.get("endTime")

        # Create or update main GPD record
        gpd_obj, created = GPD.objects.update_or_create(
            bro_id=gpd_data.get("brocom:broId", None),
            data_owner=self.data_owner,
            defaults={
                "delivery_accountable_party": gpd_data.get(
                    "brocom:deliveryAccountableParty", None
                ),
                "quality_regime": gpd_data.get("brocom:qualityRegime", None),
                "start_time": datetime.datetime.fromisoformat(start_time).date()
                if start_time
                else None,
                "end_time": datetime.datetime.fromisoformat(end_time).date()
                if end_time
                else None,
            },
        )

        # Process reports
        reports = gpd_data.get("report", [])
        if isinstance(reports, dict):
            reports = [reports]  # Convert single report to list

        for report_data in reports:
            report_obj = report_data.get("gpdcommon:Report", {})

            # Extract report period
            report_period = report_obj.get("gpdcommon:reportPeriod", {})
            report_begin = report_period.get("brocom:beginDate")
            report_end = report_period.get("brocom:endDate")

            # Get GUF reference
            guf_ref = self._extract_guf_reference(report_obj)

            # Create or update report
            report_model, created = Report.objects.update_or_create(
                gpd=gpd_obj,
                report_id=report_obj.get("gpdcommon:reportId"),
                data_owner=self.data_owner,
                defaults={
                    "method": report_obj.get("gpdcommon:method", "onbekend"),
                    "begin_date": datetime.datetime.fromisoformat(report_begin).date()
                    if report_begin
                    else None,
                    "end_date": datetime.datetime.fromisoformat(report_end).date()
                    if report_end
                    else None,
                    "groundwater_usage_facility_bro_id": guf_ref or "",
                },
            )

            # Process volume series for this report
            volume_series_list = report_obj.get("gpdcommon:volumeSeries", [])
            if isinstance(volume_series_list, dict):
                volume_series_list = [volume_series_list]  # Convert single item to list

            for vs_data in volume_series_list:
                # Extract period
                vs_period = vs_data.get("gpdcommon:period", {})
                vs_begin = vs_period.get("brocom:beginDate")
                vs_end = vs_period.get("brocom:endDate")

                # Extract volume and other attributes
                volume_data = vs_data.get("gpdcommon:volume")
                if isinstance(volume_data, dict):
                    # Handle XML elements with attributes: {"#text": "value", "@uom": "m3"}
                    volume_value = (
                        float(volume_data.get("#text", 0))
                        if volume_data.get("#text")
                        else 0.0
                    )
                elif isinstance(volume_data, (str | int | float)):
                    # Handle simple text values
                    volume_value = float(volume_data) if volume_data else 0.0
                else:
                    volume_value = 0.0

                # Extract water in/out (might have codeSpace attribute)
                water_inout_data = vs_data.get("gpdcommon:waterInOut", "onbekend")
                if isinstance(water_inout_data, dict):
                    water_in_out = water_inout_data.get("#text", "onbekend")
                else:
                    water_in_out = water_inout_data or "onbekend"

                # Extract temperature (might have codeSpace attribute)
                temp_data = vs_data.get("gpdcommon:temperatureIn", "onbekend")
                if isinstance(temp_data, dict):
                    temperature_in = temp_data.get("#text", "onbekend")
                else:
                    temperature_in = temp_data or "onbekend"

                # Create or update volume series
                VolumeSeries.objects.update_or_create(
                    report=report_model,
                    begin_date=datetime.datetime.fromisoformat(vs_begin).date()
                    if vs_begin
                    else None,
                    end_date=datetime.datetime.fromisoformat(vs_end).date()
                    if vs_end
                    else None,
                    water_in_out=water_in_out,
                    data_owner=self.data_owner,
                    defaults={
                        "volume": volume_value,
                        "temperature": temperature_in,
                    },
                )

    def _extract_guf_reference(self, report_obj: dict[str, Any]) -> str | None:
        """Extract GUF BRO ID from the report installation/facility section"""
        try:
            installation = report_obj.get("gpdcommon:installationOrFacility", {})
            facility = installation.get("gpdcommon:InstallationOrFacility", {})
            related_guf = facility.get("gpdcommon:relatedGroundwaterUsageFacility", {})
            guf_facility = related_guf.get("gpdcommon:GroundwaterUsageFacility", {})
            return guf_facility.get("gpdcommon:broId")
        except (KeyError, TypeError):
            return None
