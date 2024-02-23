import streamlit as st
import authentication as auth
import utils
import config
from components.general import sidebar


def main():
    if auth.is_authenticated():
        # Setup the session state, and page settings
        config.set_page_config()
        utils.set_user_details()

        # Sidebar
        with st.sidebar:
            sidebar()

        st.map()


if __name__ == "__main__":
    main()
