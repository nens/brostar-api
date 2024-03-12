import geopandas as gpd
import leafmap.foliumap as foliumap
import pandas as pd
import utils
from shapely.geometry import Point

import streamlit as st


def map() -> None:
    """Map component"""

    # Import Data
    gmn_df = utils.get_endpoint_data("gmn/gmns")
    measuringpoint_df = utils.get_endpoint_data("gmn/measuringpoints")
    gmw_df = utils.get_endpoint_data("gmw/gmws")

    if gmn_df.empty or measuringpoint_df.empty or gmw_df.empty:
        st.text(
            "Om de kaart te laten werken moeten er minimaal 1 GMN, en minimaal 1 GMW geimporteerd zijn."
        )

    else:
        # Select GMN
        gmn_options = gmn_df["name"].tolist()
        gmn_options = ["Selecteer een Meetnet"] + gmn_options

        selected_gmn = st.selectbox("Selecteer een GMN:", options=gmn_options)

        if not selected_gmn == "Selecteer een Meetnet":
            selected_gmn_uuid = gmn_df.loc[
                gmn_df["name"] == selected_gmn, "uuid"
            ].values[0]

            # Filter measuringpoint df
            measuringpoint_df = measuringpoint_df[
                measuringpoint_df["gmn"] == selected_gmn_uuid
            ]

            # filter GMW df based on selected GMN
            gmw_df = pd.merge(
                measuringpoint_df,
                gmw_df,
                left_on="gmw_bro_id",
                right_on="bro_id",
                how="inner",
            )

        # Transform GMW df
        gmw_df[["lat", "long"]] = gmw_df["standardized_location"].str.split(expand=True)
        geometry = [Point(xy) for xy in zip(gmw_df["long"], gmw_df["lat"])]
        geo_gmw_df = gpd.GeoDataFrame(gmw_df, geometry=geometry)
        geo_gmw_df.drop(columns=["lat", "long"], inplace=True)

        m = foliumap.Map()

        m.add_gdf(geo_gmw_df, layer_name="GMWs")

        m.to_streamlit()
