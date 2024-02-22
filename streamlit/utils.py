from typing import Dict
import requests
import streamlit as st

import config

def set_user_details() -> Dict[str, str]:
    """Saves the user details to the session state."""
    user_details = get_user_details()
    st.session_state.credentials_set = user_details["credentials_set"]
    st.session_state.organisation_name = user_details["organisation_name"]
    st.session_state.default_project_number = user_details["default_project_number"]

def get_user_details():
    """Retreives userprofile information from the api."""
    url = f"{config.BASE_URL}/api/userprofile"

    headers = {
        "Authorization": f"Bearer {st.session_state.api_token}"
    }

    r = requests.get(
        url=url,
        headers=headers,
    )

    return r.json()["results"][0]