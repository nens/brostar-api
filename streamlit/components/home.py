import streamlit as st
import utils
import config


def import_information() -> None:
    st.subheader("BRO-data import informatie")

    # Most recent import time element
    most_recent_import_datetime = utils.lookup_most_recent_datetime("importtasks")
    most_recent_import_str = most_recent_import_datetime.strftime(
        "%d-%m-%y om %H:%M:%S"
    )
    st.markdown("**Meest recente data import vanuit de BRO:**")
    st.text(most_recent_import_str)

    if st.button("Start nieuwe import taak"):
        with st.form(key="start-new-import-task"):
            # Start import task element
            st.markdown("**Importeer de huidige informatie uit de BRO:**")
            help_text = "GMN importeert GMN's en Meetpunten, GMW importeer GMW's en Monitoringbuizen"
            kvk_number = st.text_input(
                "Importeer voor kvk (default is eigen organisatie):",
                value=st.session_state.organisation_kvk,
            )
            domains_to_import = st.multiselect(
                "BRO domeinen om te importeren:",
                options=config.CURRENT_SUPPORTED_BRO_DOMAINS,
                default=config.CURRENT_SUPPORTED_BRO_DOMAINS,
                help=help_text,
            )

            st.form_submit_button(
                "Start de import taak",
                on_click=utils.start_import_tasks,
                args=domains_to_import,
                kwargs={"kvk_number": kvk_number},
            )

    if "import_task_started" in st.session_state:
        if st.session_state["import_task_started"]:
            st.success("De import taak is succesvol aangemaakt", icon="✅")
        else:
            st.warning(
                "Er heeft in het afgelopen uur al een import taak gedraaid. Om overbelasting van de BRO te voorkomen is er maar 1 taak per uur mogelijk.",
                icon="⚠️",
            )


def asset_count_metrics() -> None:
    """Gets the asset counts from the api and shows it in a matrix of metrics"""
    st.subheader("Aantal objecten in de BRO")

    asset_endpoints = [
        "gmn/gmns",
        "gmn/measuringpoints",
        "gmw/gmws",
        "gmw/monitoringtubes",
    ]
    counts = {
        endpoint: utils.get_endpoint_count(endpoint) for endpoint in asset_endpoints
    }

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("GMN's", counts["gmn/gmns"])
    col2.metric("Meetpunten", counts["gmn/measuringpoints"])
    col3.metric("GMW's", counts["gmw/gmws"])
    col4.metric("Monitoringbuizen", counts["gmw/monitoringtubes"])
