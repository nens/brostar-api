import requests
import xmltodict

from abc import ABC, abstractmethod
from typing import IO, Dict, Any, List, Tuple

from django.conf import settings
from gmn.models import GMN, Measuringpoint


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

    def __init__(self, bro_domain, bro_id) -> None:
        self.bro_domain = bro_domain
        self.bro_id = bro_id

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

    def _convert_xml_to_json(self, xml_data: IO[bytes]) -> Dict[str, Any]:
        json_data = xmltodict.parse(xml_data)

        return json_data

    @abstractmethod
    def _save_data_to_database(self, json_data: Dict[str, Any]):
        """Saves the downloaded BRO data into the Django database."""
        pass


class GMNObjectImporter(ObjectImporter):
    def _save_data_to_database(self, json_data: Dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If GMN_PPO is not found, it basically means that the object is not relevant anymore
        if not "GMN_PPO" in dispatch_document_data:
            return

        gmn_data, measuringpoint_data = self._split_json_data(dispatch_document_data)

        self._save_gmn_data(gmn_data)
        self._save_measuringpoint_data(measuringpoint_data)

    def _split_json_data(
        self, dispatch_document_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Takes in the json data and splits it up into GMN and Measuringpoint data"""

        measuringpoint_data = dispatch_document_data["GMN_PPO"].get(
            "measuringPoint", []
        )

        gmn_data = dispatch_document_data["GMN_PPO"]
        gmn_data.pop("measuringPoint", None)

        return gmn_data, measuringpoint_data

    def _save_gmn_data(self, gmn_data: Dict[str, Any]) -> None:
        self.gmn_obj, created = GMN.objects.update_or_create(
            bro_id=gmn_data.get("brocom:broId", None),
            delivery_accountable_party=gmn_data.get(
                "brocom:deliveryAccountableParty", None
            ),
            quality_regime=gmn_data.get("brocom:qualityRegime", None),
            name=gmn_data.get("name", None),
            delivery_context=gmn_data.get("deliveryContext", {}).get("#text", None),
            monitoring_purpose=gmn_data.get("monitoringPurpose", {}).get("#text", None),
            groundwater_aspect=gmn_data.get("groundwaterAspect", {}).get("#text", None),
            start_date_monitoring=gmn_data.get("monitoringNetHistory", {})
            .get("startDateMonitoring", {})
            .get("brocom:date", None),
            object_registration_time=gmn_data.get("registrationHistory", {}).get(
                "brocom:objectRegistrationTime", None
            ),
            registration_status=gmn_data.get("registrationHistory", {})
            .get("brocom:registrationStatus", {})
            .get("#text", None),
        )

        self.gmn_obj.save()

    def _save_measuringpoint_data(self, measuringpoint_data: Dict[str, Any]) -> None:
        for measuringpoint in measuringpoint_data:
            mp_data = measuringpoint.get("MeasuringPoint", {})
            monitoring_tube_data = mp_data.get("monitoringTube", {}).get(
                "GroundwaterMonitoringTube", {}
            )

            measuringpoint_obj, created = Measuringpoint.objects.update_or_create(
                gmn=self.gmn_obj,
                measuringpoint_code=mp_data.get("measuringPointCode", None),
                measuringpoint_start_date=mp_data.get("startDate", {}).get(
                    "brocom:date", None
                ),
                gmw_bro_id=monitoring_tube_data.get("broId", None),
                tube_number=monitoring_tube_data.get("tubeNumber", None),
                tube_start_date=monitoring_tube_data.get("startDate", None).get(
                    "brocom:date", None
                ),
            )

            measuringpoint_obj.save()


class GMWObjectImporter(ObjectImporter):
    def _save_data_to_database(self, json_data: Dict[str, Any]) -> None:
        dispatch_document_data = json_data.get("dispatchDataResponse", {}).get(
            "dispatchDocument", {}
        )

        # If GMW_PPO is not found, it basically means that the object is not relevant anymore
        if not "GMW_PPO" in dispatch_document_data:
            return

        gmw_data, monitoringtubes_data = self._split_json_data(dispatch_document_data)

        self._save_gmw_data(gmw_data)
        self._save_monitoringtubes_data(monitoringtubes_data)

    def _split_json_data(
        self, dispatch_document_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Takes in the json data and splits it up into GMW and tubes data"""

        monitoringtubes_data = dispatch_document_data["GMW_PPO"].get(
            "monitoringTube", []
        )

        gmw_data = dispatch_document_data["GMW_PPO"]
        gmw_data.pop("monitoringTube", None)

        return gmw_data, monitoringtubes_data

    def _save_gmw_data(self, gmw_data: Dict[str, Any]) -> None:
        pass

    def _save_monitoringtubes_data(self, monitoringtubes_data) -> None:
        pass


class GLDObjectImporter(ObjectImporter):
    pass


class FRDObjectImporter(ObjectImporter):
    pass
