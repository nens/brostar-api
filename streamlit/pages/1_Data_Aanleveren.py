import streamlit as st
import authentication as auth
import utils
import config
from components.general import sidebar
from components import delivery as components


def main():
    if auth.is_authenticated():
        # Setup the session state, and page settings
        config.set_page_config()
        utils.set_user_details()

        # Sidebar
        with st.sidebar:
            sidebar()

        if not st.session_state.credentials_set:
            st.warning("De BRO user token en password zijn niet ingesteld. Vul deze in de sidebar in om gegevens aan te kunnen leveren.", icon="⚠️")

        else:
            components.delivery()

if __name__ == "__main__":
    main()
