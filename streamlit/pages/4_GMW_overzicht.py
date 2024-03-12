import authentication as auth
import config
import utils
from components import gmw as components
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

        st.title("GMW Data")

        st.subheader("Grondwatermonitoringputten")
        components.gmw_table()

        st.subheader("Monitoringbuizen")
        components.monitoringtubes_table()


if __name__ == "__main__":
    main()
