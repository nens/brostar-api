import authentication as auth
import config
import utils
from components import home as components
from components.general import sidebar

import streamlit as st


def main():
    if auth.is_authenticated():
        # Setup the session state, and page settings
        config.set_page_config()
        utils.set_user_details()

        # Sidebar
        with st.sidebar:
            sidebar()

        # Dashboard
        st.title(f"Dashboard - {st.session_state.organisation_name}")
        st.divider()
        components.asset_count_metrics()
        st.divider()
        components.import_information()
        st.divider()
        components.upload_information()


if __name__ == "__main__":
    main()
