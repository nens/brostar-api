from lxml import etree
from lxml.etree import _Element, tostring

from .. import config
from .base_generator import XMLGenerator

class GMNStartregistration(XMLGenerator):
    """Generates a XML file for the 01_GMN_StartRegistration."""
    def __init__(self, request_type: str, metadata: dict, srcdocdata: dict) -> None:
        super().__init__(request_type, metadata, srcdocdata)
        self.namespace = config.declaration_mapping[self.request_type]
        self.xsi_schema_location = config.xsi_schemalocation
        self.id_count = 1
    
    def _create_sourcedocument(self):
        """Example XML for register:
        https://www.bro-productomgeving.nl/__attachments/159095997/01_GMN_StartRegistration.xml?inst-v=6362ee09-a77d-4052-8ab8-caf3a373ad16
        """
        # Create main sourcedocs element
        main_element = etree.Element(
            f'{{{config.gmn}}}GMN_StartRegistration'
        )
        main_element.set(
            f"{{{config.gml}}}id", f"id_000{self.id_count}"
        )
        self.id_count += 1

        # Create object id accountable party element
        object_id_accountable_party_element = etree.SubElement(
            main_element,
            "objectIdAccountableParty",
        )
        object_id_accountable_party_element.text = self.sourcedocs_data["objectIdAccountableParty"]

        # Create name element
        name_element = etree.SubElement(
            main_element,
            "name",
        )
        name_element.text = self.sourcedocs_data["name"]
        
        # Create delivery context element
        delivery_context_element = etree.SubElement(
            main_element,
            "deliveryContext",
            attrib={"codeSpace": "urn:bro:frd:EvaluationProcedure"},
        )
        delivery_context_element.text = self.sourcedocs_data["deliveryContext"]

        # Create monitoring purpose element
        monitoring_purpose_element = etree.SubElement(
            main_element,
            "monitoringPurpose",
            attrib={"codeSpace": "urn:bro:frd:EvaluationProcedure"},
        )
        monitoring_purpose_element.text = self.sourcedocs_data["monitoringPurpose"]

        # Create groundwater aspect element
        groundwater_aspect_element = etree.SubElement(
            main_element,
            "groundwaterAspect",
            attrib={"codeSpace": "urn:bro:frd:EvaluationProcedure"},
        )
        groundwater_aspect_element.text = self.sourcedocs_data["groundwaterAspect"]

        # Create startdate monitoring element
        startdate_monitoring_element = etree.SubElement(
            main_element,
            "startDateMonitoring",
        )

        startdate_date_element = etree.SubElement(
            startdate_monitoring_element,
           f"{{{config.brocom}}}date",
        )
        startdate_date_element.text = self.sourcedocs_data["startDateMonitoring"]

        # Add measuringpoints
        for measuringpoint in self.sourcedocs_data["measuringPoints"]:
            # Main element
            measuringpoint_main_element = etree.SubElement(
                main_element,
                "measuringPoint",
            )

            # Sub element
            measuringpoint_sub_element = etree.SubElement(
                measuringpoint_main_element,
                "MeasuringPoint",
            )
            measuringpoint_sub_element.set(
                f"{{{config.gml}}}id", f"id_000{self.id_count}"
            )
            self.id_count += 1

            measuringpoint_code_element = etree.SubElement(
                measuringpoint_sub_element,
                "measuringPointCode",
            )
            measuringpoint_code_element.text = measuringpoint["measuringPointCode"]
            
            # monitoringTube element
            monitoring_tube_element = etree.SubElement(
                measuringpoint_sub_element,
                "monitoringTube",
            )

            # GroundwaterMonitoringTube element
            groundwater_monitoring_tube_element = etree.SubElement(
                monitoring_tube_element,
                "GroundwaterMonitoringTube",
            )
            groundwater_monitoring_tube_element.set(
                f"{{{config.gml}}}id", f"id_000{self.id_count}"
            )
            self.id_count += 1

            bro_id_element = etree.SubElement(
                groundwater_monitoring_tube_element,
                "broId",
            )
            bro_id_element.text = measuringpoint["broId"]
            
            tube_number_element = etree.SubElement(
                groundwater_monitoring_tube_element,
                "tubeNumber",
            )
            tube_number_element.text = measuringpoint["tubeNumber"]


        # Add startregistration to sourcedocs
        self.source_document.append(main_element)
