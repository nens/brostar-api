def merge_dictionaries(dicts: list[dict]) -> dict:
    dictionaries = {}
    for dict in dicts:
        dictionaries.update(dict)
    return dictionaries


# =============================================================================
# GMW
# =============================================================================
ns_reg_gmw = {
    "": "http://www.broservices.nl/xsd/dsgmw/1.1",
    "brocom": "http://www.broservices.nl/xsd/brocommon/3.0",
    "gmwcom": "http://www.broservices.nl/xsd/gmwcommon/1.1",
    "gml": "http://www.opengis.net/gml/3.2",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

codespace_gmw = {
    "deliveryContext": "urn:bro:gmw:DeliveryContext",
    "constructionStandard": "urn:bro:gmw:ConstructionStandard",
    "initialFunction": "urn:bro:gmw:InitialFunction",
    "wellHeadProtector": "urn:bro:gmw:WellHeadProtector",
    "horizontalPositioningMethod": "urn:bro:gmw:HorizontalPositioningMethod",
    "groundLevelPositioningMethod": "urn:bro:gmw:GroundLevelPositioningMethod",
    "tubeType": "urn:bro:gmw:TubeType",
    "tubeStatus": "urn:bro:gmw:TubeStatus",
    "tubeTopPositioningMethod": "urn:bro:gmw:TubeTopPositioningMethod",
    "tubePackingMaterial": "urn:bro:gmw:TubePackingMaterial",
    "tubeMaterial": "urn:bro:gmw:TubeMaterial",
    "glue": "urn:bro:gmw:Glue",
    "sockMaterial": "urn:bro:gmw:SockMaterial",
    "electrodePackingMaterial": "urn:bro:gmw:ElectrodePackingMaterial",
    "electrodeStatus": "urn:bro:gmw:ElectrodeStatus",
    "localVerticalReferencePoint": "urn:bro:gmw:LocalVerticalReferencePoint",
    "wellStability": "urn:bro:gmw:WellStability",
    "correctionReason": "urn:bro:gmw:CorrectionReason",
}


# =============================================================================
# GMN
# =============================================================================
ns_reg_gmn1 = {"xmlns": "http://www.broservices.nl/xsd/dsgmn/1.0"}

ns_reg_gmn2 = {
    "": "http://www.broservices.nl/xsd/dsgmn/1.0",
    "brocom": "http://www.broservices.nl/xsd/brocommon/3.0",
    "gml": "http://www.opengis.net/gml/3.2",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

xsi_reg_gmn = {
    "schemaLocation": "http://www.broservices.nl/xsd/dsgmn/1.0 https://schema.broservices.nl/xsd/isgmn/1.0/isgmn-messages.xsd"
}

ns_reg_gmn_tot = merge_dictionaries([ns_reg_gmn1, ns_reg_gmn2, xsi_reg_gmn])

codespace_gmn = {
    "deliveryContext": "urn:bro:gmn:DeliveryContext",
    "monitoringPurpose": "urn:bro:gmn:MonitoringPurpose",
    "groundwaterAspect": "urn:bro:gmn:GroundwaterAspect",
    "correctionReason": "urn:bro:gmn:CorrectionReason",
}


# =============================================================================
# GLD
# =============================================================================
ns_reg_gld1 = {"xmlns": "http://www.broservices.nl/xsd/dsgld/1.0"}

ns_reg_gld2 = {
    "": "http://www.broservices.nl/xsd/dsgld/1.0",
    "brocom": "http://www.broservices.nl/xsd/brocommon/3.0",
    "gldcom": "http://www.broservices.nl/xsd/gldcommon/1.0",
    "gml": "http://www.opengis.net/gml/3.2",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

ns_reg_gld3 = {
    "wml2": "http://www.opengis.net/waterml/2.0",
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "om": "http://www.opengis.net/om/2.0",
    "swe": "http://www.opengis.net/swe/2.0",
    "xlink": "http://www.w3.org/1999/xlink",
    "brocom": "http://www.broservices.nl/xsd/brocommon/3.0",
    "gldcom": "http://www.broservices.nl/xsd/gldcommon/1.0",
    "gml": "http://www.opengis.net/gml/3.2",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

ns_reg_gld_tot = merge_dictionaries([ns_reg_gld1, ns_reg_gld2, ns_reg_gld3])

xsi_reg_gld = {
    "schemaLocation": "http://www.broservices.nl/xsd/isgld/1.0 https://schema.broservices.nl/xsd/isgld/1.0/isgld-messages.xsd"
}

codespace_gld = {
    "codeList": "urn:ISO:19115:CI_RoleCode",
    "principalInvestigator": "urn:bro:gld:ObservationMetadata:principalInvestigator",
    "observationType": "urn:bro:gld:ObservationMetadata:observationType",
    "ObservationType": "urn:bro:gld:ObservationType",
    "StatusCode": "urn:bro:gld:StatusCode",
    "airPressureCompensationType": "urn:bro:gld:ObservationProcess:airPressureCompensationType",
    "AirPressureCompensationType": "urn:bro:gld:AirPressureCompensationType",
    "evaluationProcedure": "urn:bro:gld:ObservationProcess:evaluationProcedure",
    "EvaluationProcedure": "urn:bro:gld:EvaluationProcedure",
    "measurementInstrumentType": "urn:bro:gld:ObservationProcess:measurementInstrumentType",
    "MeasurementInstrumentType": "urn:bro:gld:MeasurementInstrumentType",
    "ProcessReference": "urn:bro:gld:ProcessReference",
    "StatusQualityControl": "urn:bro:gld:StatusQualityControl",
    "censoringLimitvalue": "urn:bro:gld:PointMetadata:censoringLimitvalue",
}
