import time
import xml.etree.ElementTree as ET

import requests

from .namespaces import (
    ns_reg_gmw,
)


def _request_bro_xml(
    bro_id: str, query_params: str, type: str, bro_url: str
) -> bytes | None:
    options = ["gmw", "frd", "gar", "gmn", "gld"]
    if type.lower() not in options:
        raise Exception(f"Unknown type: {type}. Use a correct option: {options}.")

    retry = 0
    while retry < 3:
        # Try to get a response with statuscode 200 (deal with temporary time-out of servicedesk)
        res = requests.get(f"{bro_url}gm/{type}/v1/objects/{bro_id}?{query_params}")

        if res.status_code < 300:
            return res.content

        retry += 1
        time.sleep(10)
    res.raise_for_status()
    return


class GMWXML:
    def __init__(
        self,
        bro_id: str,
        bro_url: str,
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
            self.xml_content = _request_bro_xml(
                bro_id, f"fullHistory={fh}", "gmw", bro_url
            )
            self.xml_etree = ET.fromstring(self.xml_content)
        else:
            raise ValueError(f"Incorrect GMW-ID: {bro_id}")

    @property
    def gmw_construction(self) -> dict:
        """
        Format GMW data to match the GMWConstruction Pydantic model structure.
        Returns a dictionary that can be used to instantiate a GMWConstruction model.
        """
        # Format delivered location as WKT POINT string
        delivered_loc = self.delivered_location
        delivered_location_wkt = f"POINT({delivered_loc['X']} {delivered_loc['Y']})"

        # Format monitoring tubes
        formatted_tubes = []
        for tube in self.monitoring_tubes:
            formatted_tube = {
                "tubeNumber": int(tube["tubeNumber"]),
                "tubeType": tube["tubeType"],
                "artesianWellCapPresent": tube["artesianWellCapPresent"],
                "sedimentSumpPresent": tube["sedimentSumpPresent"],
                "numberOfGeoOhmCables": tube["numberOfGeoOhmCables"],
                "tubeTopDiameter": int(tube["tubeTopDiameter"])
                if tube.get("tubeTopDiameter")
                else None,
                "variableDiameter": tube.get("variableDiameter"),
                "tubeStatus": tube["tubeStatus"],
                "tubeTopPosition": float(tube["tubeTopPosition"]),
                "tubeTopPositioningMethod": tube["tubeTopPositioningMethod"],
                "tubePackingMaterial": tube["tubePackingMaterial"],
                "tubeMaterial": tube["tubeMaterial"],
                "glue": tube["glue"],
                "screenLength": float(tube["screenLength"]),
                "screenProtection": None,  # Not available in current XML structure
                "sockMaterial": tube["sockMaterial"],
                "plainTubePartLength": float(tube["plainTubePartLength"]),
                "sedimentSumpLength": float(tube["sedimentSumpLength"])
                if tube.get("sedimentSumpLength")
                else None,
            }

            # Format geo-ohm cables if present
            if tube.get("geoOhmCables"):
                formatted_cables = []
                for cable in tube["geoOhmCables"]:
                    formatted_electrodes = []
                    for electrode in cable["electrodes"]:
                        formatted_electrode = {
                            "electrodeNumber": int(electrode["electrodeNumber"]),
                            "electrodePackingMaterial": electrode[
                                "electrodePackagingMaterial"
                            ],
                            "electrodeStatus": electrode["electrodeStatus"],
                            "electrodePosition": float(electrode["electrodePosition"])
                            if electrode.get("electrodePosition")
                            else None,
                        }
                        formatted_electrodes.append(formatted_electrode)

                    formatted_cable = {
                        "cableNumber": int(cable["cableNumber"]),
                        "electrodes": formatted_electrodes,
                    }
                    formatted_cables.append(formatted_cable)

                formatted_tube["geoOhmCables"] = formatted_cables
            else:
                formatted_tube["geoOhmCables"] = None

            formatted_tubes.append(formatted_tube)

        # Build the main construction dictionary
        construction_data = {
            "objectIdAccountableParty": self.well_code,  # Using well_code as identifier
            "deliveryContext": self.delivery_context,
            "constructionStandard": self.construction_standard,
            "initialFunction": self.initial_function,
            "numberOfMonitoringTubes": self.number_of_monitoring_tubes,
            "groundLevelStable": self.ground_level_stable,
            "nitgCode": self.nitg_code,
            "wellStability": self.well_stability,
            "owner": self.owner,
            "maintenanceResponsibleParty": self.maintenance_responsible_party,
            "wellHeadProtector": self.well_head_protector,
            "wellConstructionDate": self.construction_date,
            "deliveredLocation": delivered_location_wkt,
            "horizontalPositioningMethod": delivered_loc["horizontalPositioningMethod"],
            "localVerticalReferencePoint": self.vertical_ref_point or "NAP",
            "offset": float(self.offset) if self.offset else 0.000,
            "verticalDatum": self.vertical_datum or "NAP",
            "groundLevelPosition": float(self.ground_level_pos)
            if self.ground_level_pos
            else None,
            "groundLevelPositioningMethod": self.ground_level_pos_method,
            "monitoringTubes": formatted_tubes,
            "dateToBeCorrected": None,  # Not available in current XML structure
        }

        return construction_data

    @property
    def bro_id(self) -> str | None:
        return self.xml_etree.find(".//brocom:broId", ns_reg_gmw).text

    @property
    def delivery_accountable_party(self) -> str | None:
        return self.xml_etree.find(
            ".//brocom:deliveryAccountableParty", ns_reg_gmw
        ).text

    @property
    def quality_regime(self) -> str | None:
        return self.xml_etree.find(".//brocom:qualityRegime", ns_reg_gmw).text

    @property
    def delivery_context(self) -> str | None:
        return self.xml_etree.find(".//deliveryContext", ns_reg_gmw).text

    @property
    def construction_standard(self) -> str | None:
        return self.xml_etree.find(".//constructionStandard", ns_reg_gmw).text

    @property
    def initial_function(self) -> str | None:
        return self.xml_etree.find(".//initialFunction", ns_reg_gmw).text

    @property
    def maintenance_responsible_party(self) -> str | None:
        try:
            return self.xml_etree.find(
                ".//maintenanceResponsibleParty", ns_reg_gmw
            ).text
        except AttributeError:
            return None

    @property
    def ground_level_stable(self) -> str | None:
        return self.xml_etree.find(".//groundLevelStable", ns_reg_gmw).text

    @property
    def well_stability(self) -> str | None:
        try:
            return self.xml_etree.find(".//wellStability", ns_reg_gmw).text
        except AttributeError:
            return None

    @property
    def nitg_code(self) -> str | None:
        try:
            return self.xml_etree.find(".//nitgCode", ns_reg_gmw).text
        except AttributeError:
            return None

    @property
    def well_code(self) -> str | None:
        return self.xml_etree.find(".//wellCode", ns_reg_gmw).text

    @property
    def owner(self) -> str | None:
        return self.xml_etree.find(".//owner", ns_reg_gmw).text

    @property
    def removed(self) -> str | None:
        return self.xml_etree.find(".//removed", ns_reg_gmw).text

    @property
    def well_head_protector(self) -> str | None:
        return self.xml_etree.find(".//wellHeadProtector", ns_reg_gmw).text

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

    def _location_pos(self, element: ET.Element) -> str | None:
        return element.find(".//gml:pos", ns_reg_gmw).text

    def _location_horizontal_positioning_method(
        self, element: ET.Element
    ) -> str | None:
        return element.find(".//gmwcom:horizontalPositioningMethod", ns_reg_gmw).text

    @property
    def delivered_location(self) -> dict:
        """
        Dictionary with CRS EPSG (28992), X, Y.
        """
        delivered_location = self.xml_etree.find(".//deliveredLocation", ns_reg_gmw)
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
        return element.find(".//brocom:coordinateTransformation", ns_reg_gmw).text

    @property
    def standardized_location(self) -> dict:
        """
        Dictionary with the converted EPSG:4258, Lat, Lon, Transformation.
        """
        standardized_location = self.xml_etree.find(
            ".//standardizedLocation", ns_reg_gmw
        )
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
            return element.find(
                ".//gmwcom:localVerticalReferencePoint", ns_reg_gmw
            ).text

    @property
    def offset(self) -> str | None:
        element = self._delivered_vertical_position()
        if element is not None:
            return element.find(".//gmwcom:offset", ns_reg_gmw).text

    @property
    def vertical_datum(self) -> str | None:
        element = self._delivered_vertical_position()
        if element is not None:
            return element.find(".//gmwcom:verticalDatum", ns_reg_gmw).text

    @property
    def ground_level_pos(self) -> str | None:
        element = self._delivered_vertical_position()
        if element is not None:
            return element.find(".//gmwcom:groundLevelPosition", ns_reg_gmw).text

    @property
    def ground_level_pos_method(self) -> str | None:
        element = self._delivered_vertical_position()
        if element is not None:
            return element.find(
                ".//gmwcom:groundLevelPositioningMethod", ns_reg_gmw
            ).text

    def _tube_number(self, element: ET.Element) -> str | None:
        return element.find(".//tubeNumber", ns_reg_gmw).text

    def _tube_type(self, element: ET.Element) -> str | None:
        return element.find(".//tubeType", ns_reg_gmw).text

    def _tube_status(self, element: ET.Element) -> str | None:
        return element.find(".//tubeStatus", ns_reg_gmw).text

    def _tube_top_position(self, element: ET.Element) -> str | None:
        return element.find(".//tubeTopPosition", ns_reg_gmw).text

    def _screen_info(self, element: ET.Element) -> dict:
        screen = element.find(".//screen", ns_reg_gmw)
        return {
            "screenLength": screen.find(".//screenLength", ns_reg_gmw).text,
            "sockMaterial": screen.find(".//sockMaterial", ns_reg_gmw).text,
            "screenTopPosition": screen.find(".//screenTopPosition", ns_reg_gmw).text,
            "screenBottomPosition": screen.find(
                ".//screenBottomPosition", ns_reg_gmw
            ).text,
        }

    def _plain_tube_part_length(self, element: ET.Element) -> str | None:
        return element.find(
            ".//plainTubePart/gmwcom:plainTubePartLength", ns_reg_gmw
        ).text

    def _material_used(self, element: ET.Element) -> dict:
        material = element.find(".//materialUsed", ns_reg_gmw)
        return {
            "tubePackingMaterial": material.find(
                ".//gmwcom:tubePackingMaterial", ns_reg_gmw
            ).text,
            "tubeMaterial": material.find(".//gmwcom:tubeMaterial", ns_reg_gmw).text,
            "glue": material.find(".//gmwcom:glue", ns_reg_gmw).text,
        }

    def _electrode_info(self, element: ET.Element) -> dict:
        electrode_data = {
            "electrodeNumber": element.find(
                ".//gmwcom:electrodeNumber", ns_reg_gmw
            ).text,
            "electrodePackagingMaterial": element.find(
                ".//gmwcom:electrodePackingMaterial", ns_reg_gmw
            ).text,
            "electrodeStatus": element.find(
                ".//gmwcom:electrodeStatus", ns_reg_gmw
            ).text,
            "electrodePosition": element.find(
                ".//gmwcom:electrodePosition", ns_reg_gmw
            ).text,
        }
        return electrode_data

    def _geo_ohm_cable_info(self, element: ET.Element) -> dict:
        geo_ohm_cable_data = {
            "cableNumber": element.find(".//cableNumber", ns_reg_gmw).text,
            "cableInUse": element.find(".//cableInUse", ns_reg_gmw).text,
            "electrodes": [],
        }

        electrodes = element.findall(".//electrode", ns_reg_gmw)
        for electrode in electrodes:
            geo_ohm_cable_data["electrodes"].append(self._electrode_info(electrode))

        geo_ohm_cable_data["numberOfElectrodes"] = len(electrodes)

        return geo_ohm_cable_data

    @property
    def number_of_monitoring_tubes(self) -> int | None:
        return int(self.xml_etree.find(".//numberOfMonitoringTubes", ns_reg_gmw).text)

    def _monitoring_tube_info(self, element: ET.Element) -> dict:
        tube_info = {
            "tubeNumber": self._tube_number(element),
            "tubeType": self._tube_type(element),
            "tubeStatus": self._tube_status(element),
            "tubeTopDiameter": element.find(".//tubeTopDiameter", ns_reg_gmw).text,
            "tubeTopPosition": self._tube_top_position(element),
            "tubeTopPositioningMethod": element.find(
                ".//tubeTopPositioningMethod", ns_reg_gmw
            ).text,
            "plainTubePartLength": self._plain_tube_part_length(element),
            "artesianWellCapPresent": element.find(
                ".//artesianWellCapPresent", ns_reg_gmw
            ).text,
            "sedimentSumpPresent": element.find(
                ".//sedimentSumpPresent", ns_reg_gmw
            ).text,
            "numberOfGeoOhmCables": int(
                element.find(".//numberOfGeoOhmCables", ns_reg_gmw).text
            ),
            "variableDiameter": element.find(".//variableDiameter", ns_reg_gmw).text,
            "tubePartInserted": element.find(".//tubePartInserted", ns_reg_gmw).text,
            "tubeInUse": element.find(".//tubeInUse", ns_reg_gmw).text,
        }

        tube_info.update(self._screen_info(element))
        tube_info.update(self._material_used(element))

        if tube_info["sedimentSumpPresent"] == "ja":
            tube_info.update(
                {
                    "sedimentSumpLength": element.find(
                        ".//gmwcom:sedimentSumpLength", ns_reg_gmw
                    ).text
                }
            )

        if tube_info["tubePartInserted"] == "ja":
            tube_info.update(
                {
                    "insertedPartLength": element.find(
                        ".//gmwcom:insertedPartLength", ns_reg_gmw
                    ).text,
                    "insertedPartDiameter": element.find(
                        ".//gmwcom:insertedPartDiameter", ns_reg_gmw
                    ).text,
                    "insertedPartMaterial": element.find(
                        ".//gmwcom:insertedPartMaterial", ns_reg_gmw
                    ).text,
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
        return element.find("brocom:objectRegistrationTime", ns_reg_gmw).text

    def _registration_status(self, element: ET.Element) -> str | None:
        return element.find("brocom:registrationStatus", ns_reg_gmw).text

    def _latest_addition_time(self, element: ET.Element) -> str | None:
        latest_add = element.find("brocom:latestAdditionTime", ns_reg_gmw)
        if latest_add is not None:
            return latest_add.text

    def _corrected(self, element: ET.Element) -> str | None:
        return element.find("brocom:corrected", ns_reg_gmw).text

    def _latest_correction_time(self, element: ET.Element) -> str | None:
        latest_corr = element.find("brocom:latestCorrectionTime", ns_reg_gmw)
        if latest_corr is not None:
            return latest_corr.text

    def _under_review(self, element: ET.Element) -> str | None:
        return element.find("brocom:underReview", ns_reg_gmw).text

    def _deregistered(self, element: ET.Element) -> str | None:
        return element.find("brocom:deregistered", ns_reg_gmw).text

    def _reregistered(self, element: ET.Element) -> str | None:
        return element.find("brocom:reregistered", ns_reg_gmw).text

    @property
    def registration_history(self) -> dict:
        """
        Dictionary with object registration details, including times, status, and corrections.
        """
        registration_history = self.xml_etree.find(".//registrationHistory", ns_reg_gmw)
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
        construction_element = well_history.find(".//wellConstructionDate", ns_reg_gmw)
        construction_date = construction_element.find(".//brocom:date", ns_reg_gmw)
        if construction_date is not None:
            return construction_date.text

    @property
    def removal_date(self) -> str | None:
        well_history = self.xml_etree.find(".//wellHistory", ns_reg_gmw)
        removal_date = well_history.find(".//wellRemovalDate", ns_reg_gmw)
        if removal_date is not None:
            return removal_date.find(".//brocom:date", ns_reg_gmw).text

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

    def _tube_data(self, element: ET.Element | None) -> dict | None:
        if element is None:
            return None

        items = [
            "tubeNumber",
            "tubeTopDiameter",
            "variableDiameter",
            "tubeTopPosition",
            "tubeTopPositioningMethod",
            "tubeMaterial",
            "glue",
            "plainTubePartLength",
            "tubeStatus",
            "insertedPartLength",
            "insertedPartDiameter",
            "insertedPartMaterial",
        ]

        data = {}
        for item in items:
            if element.find(f".//{item}", ns_reg_gmw):
                data[item] = element.find(f".//{item}", ns_reg_gmw).text

        return data

    def _electrode_data(self, element: ET.Element | None) -> dict | None:
        if element is None:
            return
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
        events = []
        for event in well_history.findall(".//intermediateEvent", ns_reg_gmw):
            event_name = event.find(".//eventName", ns_reg_gmw).text
            event_date = event.find(".//eventDate/brocom:date", ns_reg_gmw).text
            well_data = self._well_data(event.find(".//wellData", ns_reg_gmw))
            tube_data = self._tube_data(event.find(".//tubeData", ns_reg_gmw))
            electrode_data = self._electrode_data(
                event.find(".//electrodeData", ns_reg_gmw)
            )

            data_dict = {
                "eventName": event_name,
                "eventDate": event_date,
            }
            if well_data is not None and len(well_data) > 0:
                data_dict.update({"wellData": well_data})
            if tube_data is not None and len(tube_data) > 0:
                data_dict.update({"tubeData": tube_data})
            if electrode_data is not None and len(electrode_data) > 0:
                data_dict.update({"electrodeData": electrode_data})

            events.append(data_dict)
        return events

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
