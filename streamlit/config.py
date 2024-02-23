import streamlit as st

def set_page_config() -> None:
    """Streamlit function to set some page settings"""
    st.set_page_config(
        page_title="BRO-Hub",
        layout="wide",
        initial_sidebar_state="expanded",
    )

BASE_URL = "http://localhost:8000"

CURRENT_SUPPORTED_BRO_DOMAINS = ["GMN", "GMW"]

CURRENT_SUPPORTED_DELIVERIES = {
    "GMN":{
        "GMN_StartRegistration":['registration', 'replace', 'remove']
    },
    "GMW":{
        "GMW_StartRegistration":['registration', 'remove']
    }
}

METADATA_FIELDS = {
    "registration_GMN_StartRegistration":[
        "requestReference",
        "deliveryAccountableParty",
        "qualityRegime",
    ],
    "registration_GMW_StartRegistration":[
        "Not yet added",
    ]
}

SOURCEDOCUMENT_FIELDS = {
    "registration_GMN_StartRegistration":[
        "objectIdAccountableParty",
        "name",
        "deliveryContext",
        "monitoringPurpose",
        "groundwaterAspect",
        "startDateMonitoring",
        "measuringPointCode",
        "broID",
        "tubeNumber",
    ],
    "registration_GMW_StartRegistration":[
        "Not yet added",
    ]
}


