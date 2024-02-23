import streamlit as st
import authentication as auth
import utils
import config
from components.general import sidebar
from components import gmn as components


def main():
    if auth.is_authenticated():
        # Setup the session state, and page settings
        config.set_page_config()
        utils.set_user_details()

        # Sidebar
        with st.sidebar:
            sidebar()

        st.title("GMN Data")

        st.subheader("Networks")
        components.gmn_table()

        st.subheader("Meetpunten")
        components.measuringpoints_table()

if __name__ == "__main__":
    main()
