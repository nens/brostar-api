import streamlit as st
import pandas as pd

import utils

def gmw_table() -> None:
    """Fetches GMW data and shows it in a table"""
    gmw_df = utils.get_endpoint_data("gmw/gmws")

    gmw_df = gmw_df[[
        "bro_id",
        "well_code",
        "quality_regime",
        "delivery_context",
        "construction_standard",
        "initial_function",
        "ground_level_stable",
        "removed",
        "well_stability",
        "nitg_code",
        "well_head_protector",
        "delivered_location",
        "local_vertical_reference_point",
        "offset",
        "vertical_datum",
        "ground_level_position",
        "standardized_location",
        "registration_status",       
    ]]

    st.dataframe(gmw_df, hide_index=True)

def monitoringtubes_table() -> None:
    """Fetches monitoringtubes data and shows it in a table"""
    monitoringtubes_df = utils.get_endpoint_data("gmw/monitoringtubes")

    monitoringtubes_df = monitoringtubes_df[[
        "gmw",
        "tube_number",
        "tube_type",
        "artesian_well_cap_present",
        "sediment_sump_present",
        "number_of_geo_ohm_cables",
        "tube_top_diameter",
        "variable_diameter",
        "tube_status", 
        "tube_top_position", 
        "tube_top_positioning_method", 
        "tube_part_inserted", 
        "tube_packing_material", 
        "tube_material", 
        "glue", 
        "screen_length", 
        "sock_material", 
        "screen_top_position", 
        "screen_bottom_position", 
        "plain_tube_part_length", 

        
        


    ]]

    st.dataframe(monitoringtubes_df, hide_index=True)