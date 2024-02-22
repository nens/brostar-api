import requests
import json
import streamlit as st

import config


def is_authenticated():
    """Returns `True` if the api token is set correctly to the session state."""
 
    def check_credentials():
        """Checks whether a password entered by the user is correct."""
        api_token = get_api_token(
            username=st.session_state["username"], password=st.session_state["password"]
        )

        update_session_state(api_token)

    if "api_token" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Gebruikersnaam", key="username")
        st.text_input(
            "Wachtwoord", type="password", on_change=check_credentials, key="password"
        )
        return False

    elif not st.session_state["api_token"]:
        # credentials not correct, show input + error.
        st.text_input("Username", key="username")
        st.text_input(
            "Password", type="password", on_change=check_credentials, key="password"
        )
        st.error("Deze gebruikersnaam/wachtwoord combinatie is incorrect", icon="⚠️")
        return False
    else:
        return True


def get_api_token(username, password):
    """Uses the username and password combination to create an API token."""
    url = f"{config.BASE_URL}/api/token/"  
    headers = {'Content-Type': 'application/json'} 
    payload = {
        "username": username,
        "password": password
    }

    try:
        r = requests.post(
            url=url,
            headers=headers,
            data=json.dumps(payload),
        )
        return r.json()["access"]
    except:
        return None

def update_session_state(api_token):
    if api_token is not None:
        st.session_state.api_token = api_token
        del st.session_state["password"]
        del st.session_state["username"]
    else:
        st.session_state["api_token"] = False