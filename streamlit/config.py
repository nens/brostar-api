import streamlit as st

BASE_URL = "http://localhost:8000"

CURRENT_SUPPORTED_BRO_DOMAINS = ["GMN", "GMW"]


def set_page_config() -> None:
    """Streamlit function to set some page settings"""
    st.set_page_config(
        page_title="BRO-Hub",
        layout="wide",
        initial_sidebar_state="expanded",
    )
