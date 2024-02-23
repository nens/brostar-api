from typing import Dict, Any
import pytz
from datetime import datetime, timedelta
import requests
import streamlit as st
import pandas as pd

import config


def set_user_details() -> None:
    """Saves the user details to the session state."""
    user_details = get_user_details()
    st.session_state.name = user_details["first_name"]
    st.session_state.credentials_set = user_details["credentials_set"]
    st.session_state.organisation_name = user_details["organisation_name"]
    st.session_state.organisation_kvk = user_details["organisation_kvk"]
    st.session_state.default_project_number = user_details["default_project_number"]
    st.session_state.user_profile_url = user_details["url"]


def get_user_details() -> Dict[str, str]:
    """Retreives userprofile information from the api."""
    url = f"{config.BASE_URL}/api/userprofile"

    r = requests.get(
        url=url,
        headers=st.session_state.headers,
    )
    r.raise_for_status()

    return r.json()["results"][0]


def patch_user_profile() -> None:
    """Updates the userprofile on the user profile enpoint."""
    payload = {}

    if st.session_state["change-default-project-number"]:
        payload["default_project_number"] = st.session_state[
            "change-default-project-number"
        ]

    if st.session_state["change-bro-user-token"]:
        payload["bro_user_token"] = st.session_state["change-bro-user-token"]

    if st.session_state["change-bro-user-password"]:
        payload["bro_user_password"] = st.session_state["change-bro-user-password"]

    r = requests.patch(
        url=st.session_state.user_profile_url,
        headers=st.session_state.headers,
        json=payload,
    )
    r.raise_for_status()

    if r.status_code == 200:
        st.toast("Wijzigingen opgeslagen", icon="✅")
    else:
        st.toast("Wijzigingen niet opgeslagen. Probeer opnieuw", icon="⚠️")
           



def get_endpoint_count(endpoint: str) -> int:
    """Gets the count on a given endpoint"""
    url = f"{config.BASE_URL}/api/{endpoint}/"

    r = requests.get(
        url=url,
        headers=st.session_state.headers,
    )
    r.raise_for_status()

    return r.json()["count"]


def lookup_most_recent_datetime(endpoint: str) -> str:
    """Checks the most recent import or upload task in the API."""
    url = f"{config.BASE_URL}/api/{endpoint}/?status=COMPLETED&kvk_number={st.session_state.organisation_kvk}"
    r = requests.get(
        url=url,
        headers=st.session_state.headers,
    )
    r.raise_for_status()

    try:
        last_update = r.json()["results"][0]["created"]
        last_update = datetime.strptime(last_update, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.utc)
        return last_update
        
    except:
        return None


def start_import_tasks() -> None:
    """Start an importtask in the api based on the provided domains.

    Only runs after a validation, where is checked whether there has been an import
    task has been done in the last hour. This is to prevent an overload on the BRO.
    """
    kvk_number = st.session_state.import_task_kvk_number


    if validate_import_request():
        url = f"{config.BASE_URL}/api/importtasks/"
        for domain in st.session_state.domains_to_import:
            r = requests.post(
                url=url,
                headers=st.session_state.headers,
                json={"bro_domain": domain, "kvk_number": kvk_number},
            )
            r.raise_for_status()

        st.toast("De import taak is succesvol aangemaakt", icon="✅")

    else:
        st.toast(
                "Er heeft in het afgelopen uur al een import taak gedraaid. Om overbelasting van de BRO te voorkomen is er maar 1 taak per uur mogelijk.",
                icon="⚠️",
            )


def validate_import_request() -> bool:
    timezone = pytz.timezone("CET")
    now = datetime.now(timezone)
    most_recent_import_datetime = lookup_most_recent_datetime("importtasks")
    print(now, most_recent_import_datetime)
    if not most_recent_import_datetime:
        return True

    check = (now - most_recent_import_datetime) > timedelta(hours=1)

    return True if check else False

def get_endpoint_data(endpoint:str) -> pd.DataFrame:
    """Retreives all import tasks from the api"""
    url = f"{config.BASE_URL}/api/{endpoint}/?limit=250"
    df_list = []

    while url:
        r = requests.get(
            url=url,
            headers=st.session_state.headers,
        )

        results = r.json()["results"]
        
        for result in results:
            df_list.append(result)

        url = r.json()["next"]
       
    return pd.DataFrame(df_list)

def start_upload_task(upload_data: Dict[str,Any]) -> None:
    """Stats an upload task to deliver information to the BRO"""
    url = f"{config.BASE_URL}/api/uploadtasks/"

    r = requests.post(
        url=url,
        headers=st.session_state.headers,
        json=upload_data,
    )
    print(r.json())

    r.raise_for_status()

    if r.status_code == 201:
        st.toast("Het aanleverproces is gestart. Controleer de voortgang op de Home pagina.", icon="✅")
    else:
        st.toast("Aanlevering gefaald.", icon="⚠️")