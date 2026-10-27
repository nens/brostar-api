import datetime
import time
import xml.etree.ElementTree as ET  # nosec B405

import requests
from defusedxml.ElementTree import fromstring

from api.bro_import.namespaces import ns_reg_gld_tot, ns_reg_gmn_tot, ns_reg_gmw


def parse_flexible_date(date_value: str | None) -> str | None:
    """Return a complete ISO date for BRO dates with partial precision."""
    if not date_value:
        return None
    try:
        if len(date_value) == 4:
            parsed_date = datetime.date(int(date_value), 1, 1)
        elif len(date_value) == 7:
            year, month = date_value.split("-")
            parsed_date = datetime.date(int(year), int(month), 1)
        else:
            parsed_date = datetime.date.fromisoformat(date_value)
    except (TypeError, ValueError):
        return None
    return parsed_date.isoformat()


def _date_text(element: ET.Element | None, namespace: dict[str, str]) -> str | None:
    if element is None:
        return None
    for date_type in ("date", "yearMonth", "year"):
        value = element.find(f".//brocom:{date_type}", namespace)
        if value is not None:
            return parse_flexible_date(value.text)
    return None


def _request_bro_xml(
    bro_id: str, query_params: str, type: str, bro_url: str
) -> ET.Element:
    options = ["gmw", "frd", "gar", "gmn", "gld"]
    if type.lower() not in options:
        raise Exception(f"Unknown type: {type}. Use a correct option: {options}.")

    retry = 0
    while retry < 3:
        # Try to get a response with statuscode 200 (deal with temporary time-out of servicedesk)
        res = requests.get(
            f"{bro_url}gm/{type}/v1/objects/{bro_id}?{query_params}", timeout=20
        )
        if res.status_code < 300:
            return fromstring(res.content)

        res.raise_for_status()

        retry += 1
        time.sleep(10)

    raise Exception(f"Failed to retrieve XML for {bro_id} after 3 attempts.")


class GMWXML:
    def __init__(
        self,
        bro_id: str,
        bro_url: str = "https://publiek.broservices.nl/",
        full_history: bool = True,
    ) -> None:
        fh = "ja" if full_history else "nee"
        if not isinstance(bro_id, str):
            raise TypeError(f"Incorrect type: {type(bro_id)}.")
        elif (
            bro_id.startswith("GMW")
            and bro_id.split("GMW")[-1].isdigit()
            and len(bro_id) == 15
        ):
            self.xml_etree = _request_bro_xml(
                bro_id, f"fullHistory={fh}", "gmw", bro_url
            )
        else:
            raise ValueError(f"Incorrect GMW-ID: {bro_id}")

    @property
    def bro_id(self) -> str:
        return getattr(self.xml_etree.find(".//brocom:broId", ns_reg_gmw), "text", "")

    @property
    def delivery_accountable_party(self) -> str:
        return getattr(
            self.xml_etree.find(".//brocom:deliveryAccountableParty", ns_reg_gmw),
            "text",
            "",
        )

    @property
    def quality_regime(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:qualityRegime", ns_reg_gmw), "text", None
        )

    @property
    def delivery_context(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//deliveryContext", ns_reg_gmw), "text", None
        )

    @property
    def construction_standard(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//constructionStandard", ns_reg_gmw), "text", None
        )

    @property
    def initial_function(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//initialFunction", ns_reg_gmw), "text", None
        )

    @property
    def maintenance_responsible_party(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//maintenanceResponsibleParty", ns_reg_gmw),
            "text",
            None,
        )

    @property
    def ground_level_stable(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//groundLevelStable", ns_reg_gmw), "text", None
        )

    @property
    def well_stability(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//wellStability", ns_reg_gmw), "text", None
        )

    @property
    def nitg_code(self) -> str | None:
        return getattr(self.xml_etree.find(".//nitgCode", ns_reg_gmw), "text", None)

    @property
    def well_code(self) -> str | None:
        return getattr(self.xml_etree.find(".//wellCode", ns_reg_gmw), "text", None)

    @property
    def owner(self) -> str | None:
        return getattr(self.xml_etree.find(".//owner", ns_reg_gmw), "text", None)

    @property
    def removed(self) -> str | None:
        return getattr(self.xml_etree.find(".//removed", ns_reg_gmw), "text", None)

    @property
    def well_head_protector(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//wellHeadProtector", ns_reg_gmw), "text", None
        )

    def _location_srs(self, element: ET.Element) -> str | None:
        # Find the location element within the specified namespace
        location_elem = element.find("gmwcom:location", ns_reg_gmw)
        if location_elem is None:
            location_elem = element.find("brocom:location", ns_reg_gmw)

        if location_elem is not None:
            # Extract the srsName attribute value
            srs_name = location_elem.attrib.get("srsName")

            if srs_name:
                # Split the srsName string to extract the EPSG code
                epsg_code = srs_name.split("::")[-1]
                return f"EPSG:{epsg_code}"

        return None

    def _location_pos(self, element: ET.Element) -> str:
        return getattr(element.find(".//gml:pos", ns_reg_gmw), "text", "0 0")

    def _location_horizontal_positioning_method(
        self, element: ET.Element
    ) -> str | None:
        return getattr(
            element.find(".//gmwcom:horizontalPositioningMethod", ns_reg_gmw),
            "text",
            None,
        )

    @property
    def delivered_location(self) -> dict:
        """
        Dictionary with CRS EPSG (28992), X, Y.
        """
        delivered_location = self.xml_etree.find(".//deliveredLocation", ns_reg_gmw)
        if delivered_location is None:
            return {}

        pos = self._location_pos(delivered_location).split(" ")
        return {
            "CRS": self._location_srs(delivered_location),
            "X": pos[0],
            "Y": pos[1],
            "horizontalPositioningMethod": self._location_horizontal_positioning_method(
                delivered_location
            ),
        }

    def _coordinate_transformation(self, element: ET.Element) -> str | None:
        return getattr(
            element.find(".//brocom:coordinateTransformation", ns_reg_gmw), "text", None
        )

    @property
    def standardized_location(self) -> dict:
        """
        Dictionary with the converted EPSG:4258, Lat, Lon, Transformation.
        """
        standardized_location = self.xml_etree.find(
            ".//standardizedLocation", ns_reg_gmw
        )
        if standardized_location is None:
            return {}

        srs = self._location_srs(standardized_location)
        pos = self._location_pos(standardized_location).split(" ")
        transform = self._coordinate_transformation(standardized_location)
        return {
            "CRS": srs,
            "Lat": pos[0],
            "Lon": pos[1],
            "Transformation": transform,
        }

    def _delivered_vertical_position(self) -> ET.Element | None:
        return self.xml_etree.find(".//deliveredVerticalPosition", ns_reg_gmw)

    @property
    def vertical_ref_point(self) -> str | None:
        element = self._delivered_vertical_position()
        if element is not None:
            return getattr(
                element.find(".//gmwcom:localVerticalReferencePoint", ns_reg_gmw),
                "text",
                None,
            )
        return None

    @property
    def offset(self) -> str | None:
        element = self._delivered_vertical_position()
        if element is not None:
            return getattr(element.find(".//gmwcom:offset", ns_reg_gmw), "text", None)
        return None

    @property
    def vertical_datum(self) -> str | None:
        element = self._delivered_vertical_position()
        if element is not None:
            return getattr(
                element.find(".//gmwcom:verticalDatum", ns_reg_gmw), "text", None
            )
        return None

    @property
    def ground_level_pos(self) -> str | None:
        element = self._delivered_vertical_position()
        if element is not None:
            return getattr(
                element.find(".//gmwcom:groundLevelPosition", ns_reg_gmw), "text", None
            )
        return None

    @property
    def ground_level_pos_method(self) -> str | None:
        element = self._delivered_vertical_position()
        if element is not None:
            return getattr(
                element.find(".//gmwcom:groundLevelPositioningMethod", ns_reg_gmw),
                "text",
                None,
            )
        return None

    def _tube_number(self, element: ET.Element) -> str | None:
        return getattr(element.find(".//tubeNumber", ns_reg_gmw), "text", None)

    def _tube_type(self, element: ET.Element) -> str | None:
        return getattr(element.find(".//tubeType", ns_reg_gmw), "text", None)

    def _tube_status(self, element: ET.Element) -> str | None:
        return getattr(element.find(".//tubeStatus", ns_reg_gmw), "text", None)

    def _tube_top_position(self, element: ET.Element) -> str | None:
        return getattr(element.find(".//tubeTopPosition", ns_reg_gmw), "text", None)

    def _screen_info(self, element: ET.Element) -> dict:
        screen = element.find(".//screen", ns_reg_gmw)
        if screen is None:
            return {}
        return {
            "screenLength": getattr(
                screen.find(".//screenLength", ns_reg_gmw), "text", None
            ),
            "sockMaterial": getattr(
                screen.find(".//sockMaterial", ns_reg_gmw), "text", None
            ),
            "screenTopPosition": getattr(
                screen.find(".//screenTopPosition", ns_reg_gmw), "text", None
            ),
            "screenBottomPosition": getattr(
                screen.find(".//screenBottomPosition", ns_reg_gmw), "text", None
            ),
        }

    def _plain_tube_part_length(self, element: ET.Element) -> str | None:
        return getattr(
            element.find(".//plainTubePart/gmwcom:plainTubePartLength", ns_reg_gmw),
            "text",
            None,
        )

    def _material_used(self, element: ET.Element) -> dict:
        material = element.find(".//materialUsed", ns_reg_gmw)
        if material is None:
            return {}
        return {
            "tubePackingMaterial": getattr(
                material.find(".//gmwcom:tubePackingMaterial", ns_reg_gmw), "text", None
            ),
            "tubeMaterial": getattr(
                material.find(".//gmwcom:tubeMaterial", ns_reg_gmw), "text", None
            ),
            "glue": getattr(material.find(".//gmwcom:glue", ns_reg_gmw), "text", None),
        }

    def _electrode_info(self, element: ET.Element) -> dict:
        return {
            "electrodeNumber": getattr(
                element.find(".//gmwcom:electrodeNumber", ns_reg_gmw), "text", None
            ),
            "electrodePackagingMaterial": getattr(
                element.find(".//gmwcom:electrodePackingMaterial", ns_reg_gmw),
                "text",
                None,
            ),
            "electrodeStatus": getattr(
                element.find(".//gmwcom:electrodeStatus", ns_reg_gmw), "text", None
            ),
            "electrodePosition": getattr(
                element.find(".//gmwcom:electrodePosition", ns_reg_gmw), "text", None
            ),
        }

    def _geo_ohm_cable_info(self, element: ET.Element) -> dict:
        geo_ohm_cable_data = {
            "cableNumber": getattr(
                element.find(".//cableNumber", ns_reg_gmw), "text", None
            ),
            "cableInUse": getattr(
                element.find(".//cableInUse", ns_reg_gmw), "text", None
            ),
            "electrodes": [],
        }

        electrodes = element.findall(".//electrode", ns_reg_gmw)
        for electrode in electrodes:
            geo_ohm_cable_data["electrodes"].append(self._electrode_info(electrode))

        geo_ohm_cable_data["numberOfElectrodes"] = len(electrodes)

        return geo_ohm_cable_data

    @property
    def number_of_monitoring_tubes(self) -> int | None:
        text = getattr(
            self.xml_etree.find(".//numberOfMonitoringTubes", ns_reg_gmw), "text", None
        )
        return int(text) if text is not None else None

    def _monitoring_tube_info(self, element: ET.Element) -> dict:
        tube_info = {
            "tubeNumber": self._tube_number(element),
            "tubeType": self._tube_type(element),
            "tubeStatus": self._tube_status(element),
            "tubeTopDiameter": getattr(
                element.find(".//tubeTopDiameter", ns_reg_gmw), "text", None
            ),
            "tubeTopPosition": self._tube_top_position(element),
            "tubeTopPositioningMethod": getattr(
                element.find(".//tubeTopPositioningMethod", ns_reg_gmw), "text", None
            ),
            "plainTubePartLength": self._plain_tube_part_length(element),
            "artesianWellCapPresent": getattr(
                element.find(".//artesianWellCapPresent", ns_reg_gmw), "text", None
            ),
            "sedimentSumpPresent": getattr(
                element.find(".//sedimentSumpPresent", ns_reg_gmw), "text", None
            ),
            "numberOfGeoOhmCables": int(
                getattr(element.find(".//numberOfGeoOhmCables", ns_reg_gmw), "text", 0)
            ),
            "variableDiameter": getattr(
                element.find(".//variableDiameter", ns_reg_gmw), "text", None
            ),
            "tubePartInserted": getattr(
                element.find(".//tubePartInserted", ns_reg_gmw), "text", None
            ),
            "tubeInUse": getattr(
                element.find(".//tubeInUse", ns_reg_gmw), "text", None
            ),
        }

        tube_info.update(self._screen_info(element))
        tube_info.update(self._material_used(element))

        if tube_info["sedimentSumpPresent"] == "ja":
            tube_info.update(
                {
                    "sedimentSumpLength": getattr(
                        element.find(".//gmwcom:sedimentSumpLength", ns_reg_gmw),
                        "text",
                        None,
                    )
                }
            )

        if tube_info["tubePartInserted"] == "ja":
            tube_info.update(
                {
                    "insertedPartLength": getattr(
                        element.find(".//gmwcom:insertedPartLength", ns_reg_gmw),
                        "text",
                        None,
                    ),
                    "insertedPartDiameter": getattr(
                        element.find(".//gmwcom:insertedPartDiameter", ns_reg_gmw),
                        "text",
                        None,
                    ),
                    "insertedPartMaterial": getattr(
                        element.find(".//gmwcom:insertedPartMaterial", ns_reg_gmw),
                        "text",
                        None,
                    ),
                }
            )

        if int(tube_info["numberOfGeoOhmCables"]) > 0:
            geo_ohm_cables = element.findall(".//geoOhmCable", ns_reg_gmw)
            tube_info["geoOhmCables"] = [
                self._geo_ohm_cable_info(cable) for cable in geo_ohm_cables
            ]

        return tube_info

    @property
    def monitoring_tubes(self) -> list[dict]:
        """
        List of dictionaries with information about each monitoring tube.
        """
        monitoring_tubes = self.xml_etree.findall(".//monitoringTube", ns_reg_gmw)
        tubes_info = [self._monitoring_tube_info(tube) for tube in monitoring_tubes]

        # Sort the list of tubes by the tubeNumber key
        return sorted(tubes_info, key=lambda x: int(x["tubeNumber"]))

    def _registration_time(self, element: ET.Element) -> str | None:
        return getattr(
            element.find("brocom:objectRegistrationTime", ns_reg_gmw), "text", None
        )

    def _registration_status(self, element: ET.Element) -> str | None:
        return getattr(
            element.find("brocom:registrationStatus", ns_reg_gmw), "text", None
        )

    def _latest_addition_time(self, element: ET.Element) -> str | None:
        return getattr(
            element.find("brocom:latestAdditionTime", ns_reg_gmw), "text", None
        )

    def _corrected(self, element: ET.Element) -> str | None:
        return getattr(element.find("brocom:corrected", ns_reg_gmw), "text", None)

    def _latest_correction_time(self, element: ET.Element) -> str | None:
        return getattr(
            element.find("brocom:latestCorrectionTime", ns_reg_gmw), "text", None
        )

    def _under_review(self, element: ET.Element) -> str | None:
        return getattr(element.find("brocom:underReview", ns_reg_gmw), "text", None)

    def _deregistered(self, element: ET.Element) -> str | None:
        return getattr(element.find("brocom:deregistered", ns_reg_gmw), "text", None)

    def _reregistered(self, element: ET.Element) -> str | None:
        return getattr(element.find("brocom:reregistered", ns_reg_gmw), "text", None)

    @property
    def registration_history(self) -> dict:
        """
        Dictionary with object registration details, including times, status, and corrections.
        """
        registration_history = self.xml_etree.find(".//registrationHistory", ns_reg_gmw)
        if registration_history is None:
            return {}
        return {
            "objectRegistrationTime": self._registration_time(registration_history),
            "registrationStatus": self._registration_status(registration_history),
            "latestAdditionTime": self._latest_addition_time(registration_history),
            "corrected": self._corrected(registration_history),
            "latestCorrectionTime": self._latest_correction_time(registration_history),
            "underReview": self._under_review(registration_history),
            "deregistered": self._deregistered(registration_history),
            "reregistered": self._reregistered(registration_history),
        }

    @property
    def construction_date(self) -> str | None:
        well_history = self.xml_etree.find(".//wellHistory", ns_reg_gmw)
        if well_history is None:
            return None
        construction_element = well_history.find(".//wellConstructionDate", ns_reg_gmw)
        if construction_element is None:
            return None
        return getattr(
            construction_element.find(".//brocom:date", ns_reg_gmw), "text", None
        )

    @property
    def removal_date(self) -> str | None:
        well_history = self.xml_etree.find(".//wellHistory", ns_reg_gmw)
        if well_history is None:
            return None
        removal_date = well_history.find(".//wellRemovalDate", ns_reg_gmw)
        if removal_date is None:
            return None
        return getattr(removal_date.find(".//brocom:date", ns_reg_gmw), "text", None)

    def _well_data(self, element: ET.Element | None) -> dict | None:
        if element is None:
            return None

        ground_level_position = element.find(".//groundLevelPosition", ns_reg_gmw)
        ground_level_positioning_method = element.find(
            ".//groundLevelPositioningMethod", ns_reg_gmw
        )
        well_head_protector = element.find(".//wellHeadProtector", ns_reg_gmw)
        well_stability = element.find(".//wellStability", ns_reg_gmw)
        ground_level_stable = element.find(".//groundLevelStable", ns_reg_gmw)

        data = {}
        if ground_level_position is not None:
            data["groundLevelPosition"] = ground_level_position.text
        if ground_level_positioning_method is not None:
            data["groundLevelPositioningMethod"] = ground_level_positioning_method.text
        if well_head_protector is not None:
            data["wellHeadProtector"] = well_head_protector.text
        if well_stability is not None:
            data["wellStability"] = well_stability.text
        if ground_level_stable is not None:
            data["groundLevelStable"] = ground_level_stable.text

        return data

    def _tube_data(self, element: ET.Element | None) -> dict | None:  # noqa: C901
        if element is None:
            return None

        tube_number = element.find(".//tubeNumber", ns_reg_gmw)
        tube_top_diameter = element.find(".//tubeTopDiameter", ns_reg_gmw)
        variable_diameter = element.find(".//variableDiameter", ns_reg_gmw)
        tube_top_position = element.find(".//tubeTopPosition", ns_reg_gmw)
        tube_top_positioning_method = element.find(
            ".//tubeTopPositioningMethod", ns_reg_gmw
        )
        tube_material = element.find(".//tubeMaterial", ns_reg_gmw)
        glue = element.find(".//glue", ns_reg_gmw)
        plain_tube_part_length = element.find(".//plainTubePartLength", ns_reg_gmw)
        tube_status = element.find(".//tubeStatus", ns_reg_gmw)
        inserted_part_length = element.find(".//insertedPartLength", ns_reg_gmw)
        inserted_part_diameter = element.find(".//insertedPartDiameter", ns_reg_gmw)
        inserted_part_material = element.find(".//insertedPartMaterial", ns_reg_gmw)

        data = {}
        if tube_number is not None:
            data["tubeNumber"] = tube_number.text
        if tube_top_diameter is not None:
            data["tubeTopDiameter"] = tube_top_diameter.text
        if variable_diameter is not None:
            data["variableDiameter"] = variable_diameter.text
        if tube_top_position is not None:
            data["tubeTopPosition"] = tube_top_position.text
        if tube_top_positioning_method is not None:
            data["tubeTopPositioningMethod"] = tube_top_positioning_method.text
        if tube_material is not None:
            data["tubeMaterial"] = tube_material.text
        if glue is not None:
            data["glue"] = glue.text
        if plain_tube_part_length is not None:
            data["plainTubePartLength"] = plain_tube_part_length.text
        if tube_status is not None:
            data["tubeStatus"] = tube_status.text
        if inserted_part_length is not None:
            data["insertedPartLength"] = inserted_part_length.text
        if inserted_part_diameter is not None:
            data["insertedPartDiameter"] = inserted_part_diameter.text
        if inserted_part_material is not None:
            data["insertedPartMaterial"] = inserted_part_material.text

        return data

    def _electrode_data(self, element: ET.Element | None) -> dict | None:
        if element is None:
            return None

        tube_number = element.find(".//tubeNumber", ns_reg_gmw)
        cable_number = element.find(".//cableNumber", ns_reg_gmw)
        electrode_number = element.find(".//electrodeNumber", ns_reg_gmw)
        electrode_status = element.find(".//electrodeStatus", ns_reg_gmw)

        data = {}
        if tube_number is not None:
            data["tubeNumber"] = tube_number.text
        if cable_number is not None:
            data["cableNumber"] = cable_number.text
        if electrode_number is not None:
            data["electrodeNumber"] = electrode_number.text
        if electrode_status is not None:
            data["electrodeStatus"] = electrode_status.text

        return data

    @property
    def intermediate_events(self) -> list[dict]:
        well_history = self.xml_etree.find(".//wellHistory", ns_reg_gmw)
        if well_history is None:
            return []

        events = []
        for event in well_history.findall(".//intermediateEvent", ns_reg_gmw):
            event_name = getattr(event.find(".//eventName", ns_reg_gmw), "text", None)
            event_date = _date_text(event.find(".//eventDate", ns_reg_gmw), ns_reg_gmw)

            if event_name is None or event_date is None:
                continue  # Skip malformed events

            data_dict = {
                "eventName": event_name,
                "eventDate": event_date,
            }

            if well_data := self._well_data(event.find(".//wellData", ns_reg_gmw)):
                data_dict["wellData"] = well_data
            if tube_data := [
                self._tube_data(tube)
                for tube in event.findall(".//tubeData", ns_reg_gmw)
            ]:
                data_dict["tubeData"] = tube_data
            if electrode_data := [
                self._electrode_data(electrode)
                for electrode in event.findall(".//electrodeData", ns_reg_gmw)
            ]:
                data_dict["electrodeData"] = electrode_data

            events.append(data_dict)

        return events

    def _get_most_recent_value(self, data_key: str, value_key: str):
        """Extract most recent value from intermediate events by date."""
        values_by_date = {
            event["eventDate"]: event[data_key][value_key]
            for event in self.intermediate_events
            if data_key in event and value_key in event[data_key]
        }

        if not values_by_date:
            return None

        return values_by_date[max(values_by_date.keys())]

    def _get_most_recent_tube_value(
        self, data_key: str, value_key: str, tube_number: int
    ):
        """Extract most recent value for a tube from intermediate events by date."""
        # Keep only events for the specified tube number
        values_by_date = {}
        for event in self.intermediate_events:
            for tube in event.get(data_key, []):
                if tube.get("tubeNumber") == str(tube_number) and value_key in tube:
                    values_by_date[event["eventDate"]] = tube[value_key]

        if not values_by_date:
            return None

        return values_by_date[max(values_by_date.keys())]

    @property
    def most_recent_ground_level_position(self) -> float | None:
        val = self._get_most_recent_value("wellData", "groundLevelPosition")
        if val is not None:
            return float(val)

        return float(self.ground_level_pos) if self.ground_level_pos else None

    def most_recent_tube_top_position(self, tube_number: int) -> float | None:
        """Find the most recent tube top position for a specific tube number."""
        val = self._get_most_recent_tube_value(
            "tubeData", "tubeTopPosition", tube_number
        )
        if val is not None:
            return float(val)

        original_tube_position = None
        for tube in self.monitoring_tubes:
            if int(tube["tubeNumber"]) == tube_number:
                original_tube_position = (
                    float(tube["tubeTopPosition"]) if tube["tubeTopPosition"] else None
                )

        return original_tube_position

    @property
    def well_events(self) -> list[dict]:
        events = []
        for event in self.intermediate_events:
            if event.get("wellData", None):
                events.append(event)
        return events

    @property
    def tube_events(self) -> list[dict]:
        events = []
        for event in self.intermediate_events:
            if event.get("tubeData", None):
                events.append(event)
        return events

    @property
    def electrode_events(self) -> list[dict]:
        events = []
        for event in self.intermediate_events:
            if event.get("electrodeData", None):
                events.append(event)
        return events


class GLDXML:
    def __init__(
        self,
        bro_id: str,
        bro_url: str,
        start_date: str = "1900-01-01",
        end_date: str | None = None,
        filtered: bool = True,
    ) -> None:
        """
        Dates should have the following format: YYYY-MM-DD.
        """
        filter_status = "ja" if filtered else "nee"
        end_date_str = f"&observationPeriodEndDate={end_date}" if end_date else ""
        if not isinstance(bro_id, str):
            raise TypeError(f"Incorrect type: {type(bro_id)}.")
        elif (
            bro_id.startswith("GLD")
            and bro_id.split("GLD")[-1].isdigit()
            and len(bro_id) == 15
        ):
            self.xml_etree = _request_bro_xml(
                bro_id,
                f"observationPeriodBeginDate={start_date}{end_date_str}&filtered={filter_status}",
                "gld",
                bro_url,
            )
        else:
            raise ValueError(f"Incorrect GLD-ID: {bro_id}")

    @property
    def bro_id(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:broId", ns_reg_gld_tot), "text", None
        )

    @property
    def deregistered(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:deregistered", ns_reg_gld_tot), "text", None
        )

    @property
    def deregistration_time(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:deregistrationTime", ns_reg_gld_tot),
            "text",
            None,
        )

    @property
    def delivery_accountable_party(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:deliveryAccountableParty", ns_reg_gld_tot),
            "text",
            None,
        )

    @property
    def quality_regime(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:qualityRegime", ns_reg_gld_tot), "text", None
        )

    def _registration_time(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:objectRegistrationTime", ns_reg_gld_tot),
            "text",
            None,
        )

    def _registration_status(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:registrationStatus", ns_reg_gld_tot),
            "text",
            None,
        )

    def _latest_addition_time(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:latestAdditionTime", ns_reg_gld_tot),
            "text",
            None,
        )

    def _corrected(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:corrected", ns_reg_gld_tot), "text", None
        )

    def _latest_correction_time(self) -> str | None:
        latest_corr = self.xml_etree.find(
            ".//brocom:latestCorrectionTime", ns_reg_gld_tot
        )
        if latest_corr is not None:
            return latest_corr.text

    def _under_review(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:underReview", ns_reg_gld_tot), "text", None
        )

    def _deregistered(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:deregistered", ns_reg_gld_tot), "text", None
        )

    def _reregistered(self) -> str | None:
        return getattr(
            self.xml_etree.find(".//brocom:reregistered", ns_reg_gld_tot), "text", None
        )

    @property
    def registration_history(self) -> dict:
        """
        Dictionary with object registration details, including times, status, and corrections.
        """
        return {
            "objectRegistrationTime": self._registration_time(),
            "registrationStatus": self._registration_status(),
            "latestAdditionTime": self._latest_addition_time(),
            "corrected": self._corrected(),
            "latestCorrectionTime": self._latest_correction_time(),
            "underReview": self._under_review(),
            "deregistered": self._deregistered(),
            "reregistered": self._reregistered(),
        }

    def _get_monitoring_tube_info(self) -> ET.Element | None:
        return self.xml_etree.find(
            ".//gldcom:GroundwaterMonitoringTube", ns_reg_gld_tot
        )

    @property
    def gmw_bro_id(self):
        tube = self._get_monitoring_tube_info()
        if tube is None:
            return None

        return getattr(tube.find(".//gldcom:gmwBroId", ns_reg_gld_tot), "text", None)

    @property
    def tube_number(self):
        tube = self._get_monitoring_tube_info()
        if tube is None:
            return None

        return getattr(tube.find(".//gldcom:tubeNumber", ns_reg_gld_tot), "text", None)


class GMNXML:
    def __init__(
        self,
        bro_id: str,
        bro_url: str,
        full_history: bool = True,
    ) -> None:
        """
        bro_url: 'https://publiek.broservices.nl/gm/gmn/v1/'
        """
        fh = "ja" if full_history else "nee"
        if not isinstance(bro_id, str):
            raise TypeError(f"Incorrect type: {type(bro_id)}.")
        elif (
            bro_id.startswith("GMN")
            and bro_id.split("GMN")[-1].isdigit()
            and len(bro_id) == 15
        ):
            self.xml_etree = _request_bro_xml(
                bro_id, f"fullHistory={fh}", "gmn", bro_url
            )
        else:
            raise ValueError(f"Incorrect GMN-ID: {bro_id}")

    @property
    def bro_id(self) -> str | None:
        return self.xml_etree.find(".//brocom:broId", ns_reg_gmn_tot).text

    @property
    def delivery_accountable_party(self) -> str | None:
        return self.xml_etree.find(
            ".//brocom:deliveryAccountableParty", ns_reg_gmn_tot
        ).text

    @property
    def quality_regime(self) -> str | None:
        return self.xml_etree.find(".//brocom:qualityRegime", ns_reg_gmn_tot).text

    @property
    def name(self) -> str | None:
        return self.xml_etree.find(".//name", ns_reg_gmn_tot).text

    @property
    def delivery_context(self) -> str | None:
        return self.xml_etree.find(".//deliveryContext", ns_reg_gmn_tot).text

    @property
    def monitoring_purpose(self) -> str | None:
        return self.xml_etree.find(".//monitoringPurpose", ns_reg_gmn_tot).text

    @property
    def groundwater_aspect(self) -> str | None:
        return self.xml_etree.find(".//groundwaterAspect", ns_reg_gmn_tot).text

    @property
    def _monitoring_net_history(self) -> ET.Element:
        return self.xml_etree.find(".//monitoringNetHistory", ns_reg_gmn_tot)

    @property
    def start_monitoring_date(self) -> str | None:
        start_date_monitoring = self._monitoring_net_history.find(
            ".//startDateMonitoring", ns_reg_gmn_tot
        )
        return start_date_monitoring.find(".//brocom:date", ns_reg_gmn_tot).text

    @property
    def end_monitoring_date(self) -> str | None:
        end_date_monitoring = self._monitoring_net_history.find(
            ".//endDateMonitoring", ns_reg_gmn_tot
        )
        return _date_text(end_date_monitoring, ns_reg_gmn_tot)

    def _setup_event_dict(self, intermediate_event: ET.Element) -> dict:
        event_name = intermediate_event.find(".//eventName", ns_reg_gmn_tot).text
        event_date = _date_text(intermediate_event, ns_reg_gmn_tot)
        point_code = intermediate_event.find(".//measuringPointCode", ns_reg_gmn_tot)
        if point_code is not None:
            point_code = point_code.text
        return {
            "name": event_name,
            "date": event_date,
            "measuring_point_code": point_code,
        }

    @property
    def intermediate_events(self) -> list | None:
        events = self._monitoring_net_history.findall(
            ".//intermediateEvent", ns_reg_gmn_tot
        )
        event_list = []
        for event in events:
            event_list.append(self._setup_event_dict(event))
        return event_list

    def _date(self, element: ET.Element) -> str:
        return _date_text(element, ns_reg_gmn_tot)

    def _setup_monitoring_tube(self, monitoring_tube: ET.Element) -> dict:
        start_date = self._date(monitoring_tube.find(".//startDate", ns_reg_gmn_tot))
        end_date = monitoring_tube.find(".//endDate", ns_reg_gmn_tot)
        if end_date is not None:
            end_date = self._date(end_date)
        bro_id = monitoring_tube.find(".//broId", ns_reg_gmn_tot).text
        tube_nr = monitoring_tube.find(".//tubeNumber", ns_reg_gmn_tot).text
        return {
            "bro_id": bro_id,
            "tube_nr": tube_nr,
            "start_date": start_date,
            "end_date": end_date,
        }

    def _setup_measuring_point(self, measuring_point: ET.Element) -> dict:
        measuring_point_code = measuring_point.find(
            ".//measuringPointCode", ns_reg_gmn_tot
        ).text
        start_date = self._date(measuring_point.find(".//startDate", ns_reg_gmn_tot))
        monitoring_tubes = measuring_point.findall(".//monitoringTube", ns_reg_gmn_tot)
        tubes = []
        for monitoring_tube in monitoring_tubes:
            tubes.append(self._setup_monitoring_tube(monitoring_tube))
        return {
            "measuring_point_code": measuring_point_code,
            "start_date": start_date,
            "monitoring_tubes": tubes,
        }

    @property
    def measuring_points(self) -> list | None:
        monitoring_points = self.xml_etree.findall(".//MeasuringPoint", ns_reg_gmn_tot)
        measuring_points = []
        for monitoring_point in monitoring_points:
            measuring_points.append(self._setup_measuring_point(monitoring_point))
        return measuring_points
