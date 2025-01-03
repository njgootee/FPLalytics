import streamlit as st
import pandas as pd

# read app vars in
app_vars = pd.read_csv("data/app_vars.csv")
seasons = app_vars["season"]

# page config
st.set_page_config(
    page_title="Home • FPLalytics", page_icon=":chart_with_upwards_trend:"
)

# sidebar
with st.sidebar:
    st.markdown(""":chart_with_upwards_trend: :blue[FPL]*alytics*""")
    season_option = st.selectbox("Season", seasons)
    latest_gw = app_vars[app_vars["season"] == season_option]["latest_gameweek"].item()
    st.caption(
        """Latest gameweek data: :blue["""
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
st.markdown(
    "##### Latest data from Gameweek :blue["
    + str(latest_gw)
    + """] 
Use our latest data, stats, and models to prepare your team for success in Gameweek """
    + str(latest_gw + 1)
    + "."
)

# development updates
st.markdown(
"""##### Development Updates
    - Points Projections
        - Live for 2024 season
    - Fixture Ticker
        - Home/Away fixtures
    - Player Comparison dashboard updates
        - Performance stats redesign
        - Enhanced filter options
        - Historical gameweek performance comparison
        - Upcoming fixtures comparison"""
)
