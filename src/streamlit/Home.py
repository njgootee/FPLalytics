import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# read data in
odm_data = pd.read_csv("data/2023/odm_rating.csv")
latest_gw = str(odm_data["gameweek"].max() - 1)

# page config
st.set_page_config(
    page_title="Home • FPLalytics", page_icon=":chart_with_upwards_trend:"
)

# sidebar
with st.sidebar:
    st.markdown(
        """:chart_with_upwards_trend: :blue[FPL]*alytics*  
                Latest gameweek data: :blue["""
        + latest_gw
        + """]  
                [GitHub](https://github.com/njgootee)"""
    )

# landing
st.title(":chart_with_upwards_trend: :blue[FPL]*alytics*")
st.markdown(
    """**Welcome to FPLalytics - Your Ultimate Fantasy Premier League Data Companion!**

FPLalytics transforms raw fixture and player data into actionable intelligence, enabling you to make informed transfer decisions and challenge your biases.
Stay ahead of the competition with data-driven decision-making tools that are accessible, interactive, and feature rich. 

Users are strongly encouraged to complement their experience with this app by incorporating the eye-test. *Trust your instincts, and our analytics.*"""
)

# latest gameweek
st.markdown("""#### Latest data from Gameweek :blue[""" + latest_gw + "]")

# development updates
st.markdown(
    """#### Development Updates  
FPLalytics is now available to the public!"""
)
