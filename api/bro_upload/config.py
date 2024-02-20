from .xml_generators import gmn_generators

# Mapping for the determination of which xml generator should be used for a given request_type
xml_generator_mapping = {
    "GMN_StartRegistration": gmn_generators.GMNStartregistration,
}


# Declaration urls
brocom = "http://www.broservices.nl/xsd/brocommon/3.0"
gml = "http://www.opengis.net/gml/3.2"
xsi = "http://www.w3.org/2001/XMLSchema-instance"
gmn = "http://www.broservices.nl/xsd/isgmn/1.0"

gmn_xsi_schemalocation = "http://www.broservices.nl/xsd/isgmn/1.0 https://schema.broservices.nl/xsd/isgmn/1.0/isgmn-messages.xsd"

# Declaration configuration per request type
declaration_mapping = {
    "GMN_StartRegistration": {
        None: gmn,
        "brocom": brocom,
        "gml": gml,
        "xsi": xsi,
    },
}
