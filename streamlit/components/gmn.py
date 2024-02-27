import streamlit as st
import pandas as pd

import utils

def gmn_table() -> None:
    """Fetches GMN data and shows it in a table"""
    gmn_df = utils.get_endpoint_data("gmn/gmns")

    if gmn_df.empty :
        st.text("Er zijn nog geen GMNs geimporteerd.")

    else:
        gmn_df = gmn_df[[
            "bro_id",
            "delivery_accountable_party",
            "quality_regime",
            "name",
            "delivery_context",
            "monitoring_purpose",
            "groundwater_aspect",
            "start_date_monitoring",
            "registration_status",
        ]]

        st.dataframe(gmn_df, hide_index=True)

def measuringpoints_table() -> None:
    """Fetches measuringpoints data and shows it in a table"""
    measuringpoints_df = utils.get_endpoint_data("gmn/measuringpoints")
    
    if measuringpoints_df.empty :
        st.text("Er zijn nog geen meetpunten geimporteerd.")
    
    else:
    
        measuringpoints_df = measuringpoints_df[[
            "gmn",
            "measuringpoint_code",
            "measuringpoint_start_date",
            "gmw_bro_id",
            "tube_number",
            "tube_start_date",
        ]]

        st.dataframe(measuringpoints_df, hide_index=True)