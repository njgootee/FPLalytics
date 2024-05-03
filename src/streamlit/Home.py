import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# read data in
odm_data = pd.read_csv("data/2023/odm_rating.csv")
latest_gw = odm_data["gameweek"].max() - 1

# page config
st.set_page_config(
    page_title="Home • FPLalytics", page_icon=":chart_with_upwards_trend:"
)

# sidebar
with st.sidebar:
    st.markdown(
        """:chart_with_upwards_trend: :blue[FPL]*alytics*  
                Latest gameweek data: :blue["""
        + str(latest_gw)
        + """]  
                [GitHub](https://github.com/njgootee)"""
    )

# landing
st.title(":chart_with_upwards_trend: :blue[FPL]*alytics*")
st.markdown(
    """**Welcome to FPLalytics - Your Ultimate Fantasy Premier League Data Companion!**

FPLalytics transforms raw fixture and player data into actionable intelligence, enabling you to make informed transfer decisions and challenge your biases.
Stay ahead of the competition with data-driven decision-making tools that are accessible, interactive, and feature rich. 
"""
)

# latest gameweek
st.markdown("##### Latest data from Gameweek :blue[" + str(latest_gw) + """] 
Use our latest data, stats, and models to prepare your team for success in Gameweek """ + str(latest_gw + 1) + ".")

# development updates
st.markdown(
    """##### Development Updates  
- Penalty and npxG data
- FPL player naming conventions"""
)
