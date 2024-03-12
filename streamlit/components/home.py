import config
import utils

import streamlit as st


def asset_count_metrics() -> None:
    """Gets the asset counts from the api and shows it in a matrix of metrics"""
    st.subheader("Aantal objecten geimporteerd uit de BRO")

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


def import_information() -> None:
    st.subheader("BRO-data import informatie")

    # Most recent import time element
    most_recent_import_datetime = utils.lookup_most_recent_datetime("importtasks")
    if most_recent_import_datetime:
        most_recent_import_str = most_recent_import_datetime.strftime(
            "%d-%m-%y om %H:%M:%S"
        )
        st.markdown(
            "**Meest recente data import vanuit de BRO (voor eigen organisatie):**"
        )
        st.text(most_recent_import_str)
    else:
        st.info(
            "Er heeft nog geen import plaatsgevonden. Gebruik de knop hieronder voor een eerste import."
        )

    if st.button("Start nieuwe import taak"):
        with st.form(key="start-new-import-task"):
            # Start import task element
            st.markdown("**Importeer de huidige informatie uit de BRO:**")
            help_text = "GMN importeert GMN's en Meetpunten, GMW importeer GMW's en Monitoringbuizen"
            st.text_input(
                "Importeer voor kvk (default is eigen organisatie):",
                value=st.session_state.organisation_kvk,
                key="import_task_kvk_number",
            )
            st.multiselect(
                "BRO domeinen om te importeren:",
                options=config.CURRENT_SUPPORTED_BRO_DOMAINS,
                default=config.CURRENT_SUPPORTED_BRO_DOMAINS,
                help=help_text,
                key="domains_to_import",
            )

            st.form_submit_button(
                "Start de import taak",
                on_click=utils.start_import_tasks,
            )

    import_tasks = utils.get_endpoint_data(endpoint="importtasks")
    if not import_tasks.empty:
        st.markdown("**Alle uitgevoerde import taken:**")
        import_tasks = import_tasks[
            [
                "bro_domain",
                "kvk_number",
                "status",
                "created",
                "log",
            ]
        ]
        st.dataframe(import_tasks, hide_index=True)


def upload_information() -> None:
    """Upload information component"""
    st.subheader("Aanleveringen informatie")

    upload_tasks = utils.get_endpoint_data(endpoint="uploadtasks")
    if upload_tasks.empty:
        st.info("Er hebben nog geen leveringen via de API plaatsgevonden.")
    else:
        st.markdown("**Alle leveringen:**")
        upload_tasks = upload_tasks[
            [
                "bro_domain",
                "project_number",
                "registration_type",
                "request_type",
                "last_updated",
                "status",
                "log",
            ]
        ]
        st.dataframe(upload_tasks, hide_index=True)
