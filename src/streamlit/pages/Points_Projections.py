import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# read data in
projections_df = pd.read_csv("data/2023/points_projections.csv")
odm_data = pd.read_csv("data/2023/odm_rating.csv")
odm_data = odm_data.tail(20)
curr_gw = odm_data["gameweek"].max()

# page config
st.set_page_config(
    page_title="Points Projections • FPLalytics",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

# sidebar
with st.sidebar:
    st.markdown(
        """:chart_with_upwards_trend: :blue[FPL]*alytics*  
                Latest gameweek data: :blue["""
        + str(curr_gw - 1)
        + """]  
                [GitHub](https://github.com/njgootee)"""
    )

# title and information
st.title("Points Projections")
st.caption(
    ":warning: Development Build, Post-Season View",
    help="The development build uses real rather than predicted minutes. Post-season view displays the final 6 gameweeks.",
)
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to compare projected points for players and inform your transfer decisions. 
        Data tables can be downloaded, searched, and expanded with tooltip that appears on mouse hover.

Points projections are calculated by an expected value model that takes weighted historical performance statistics as inputs. 

The model considers the following:
* player historical xG performance
* player historical xA performance
* opponent team offensive and defensive strength
* home / away fixtures
* expected penalties
* goalkeeper historical saves performance
* player historical FPL bonus points

 """
    )

# options
with st.expander("Options", expanded=False):
    # Model select box
    price_filter = st.slider(
        "Max Price",
        min_value=projections_df["now_cost"].min(),
        max_value=projections_df["now_cost"].max(),
        value=projections_df["now_cost"].max(),
        step=0.1,
        format="£%.1fm",
    )

# short team names
short_name_dict = {
    "Arsenal": "ARS",
    "Aston Villa": "AVL",
    "Bournemouth": "BOU",
    "Brentford": "BRE",
    "Brighton": "BRI",
    "Burnley": "BUR",
    "Chelsea": "CHE",
    "Crystal Palace": "CRY",
    "Everton": "EVE",
    "Fulham": "FUL",
    "Liverpool": "LIV",
    "Luton": "LUT",
    "Manchester City": "MCI",
    "Manchester United": "MUN",
    "Newcastle United": "NEW",
    "Nottingham Forest": "NFO",
    "Sheffield United": "SHU",
    "Tottenham": "TOT",
    "West Ham": "WHU",
    "Wolverhampton Wanderers": "WOL",
}

# filter based on price selection
projections_df = projections_df[projections_df["now_cost"] <= price_filter]

# format team names to short versions
projections_df = projections_df.replace({"team_name": short_name_dict})

# get column names for formatting
all_columns = projections_df.columns.to_list()
display_columns = [x for x in all_columns if x not in ["player_id", "element_type"]]
gameweek_columns = [
    x
    for x in all_columns
    if x not in ["player_id", "team_name", "web_name", "now_cost", "element_type"]
]

# sort values by next gameweek projected points
projections_df = projections_df.sort_values(by=gameweek_columns[0], ascending=False)

# subset by position
forwards_df = projections_df[projections_df["element_type"] == 4]
midfielders_df = projections_df[projections_df["element_type"] == 3]
defenders_df = projections_df[projections_df["element_type"] == 2]
goalkeepers_df = projections_df[projections_df["element_type"] == 1]

# tab setup
by_pos_tab, combine_tab = st.tabs(["By Position", "Combined"])

with by_pos_tab:
    # forwards points projections visualization
    st.header("Forwards")
    st.dataframe(
        forwards_df.style.background_gradient(
            axis=0, subset=gameweek_columns, cmap="RdYlGn"
        )
        .background_gradient(axis=0, subset="now_cost", cmap="Blues")
        .format({"now_cost": "£{:.1f}m"}, precision=2),
        column_config={
            "web_name": "Player",
            "team_name": "Team",
            "now_cost": st.column_config.NumberColumn("Price", help="FPL Price"),
        },
        column_order=(display_columns),
        hide_index=True,
        use_container_width=True,
    )

    # midfielders points projections visualization
    st.header("Midfielders")
    st.dataframe(
        midfielders_df.style.background_gradient(
            axis=0, subset=gameweek_columns, cmap="RdYlGn"
        )
        .background_gradient(axis=0, subset="now_cost", cmap="Blues")
        .format({"now_cost": "£{:.1f}m"}, precision=2),
        column_config={
            "web_name": "Player",
            "team_name": "Team",
            "now_cost": st.column_config.NumberColumn("Price", help="FPL Price"),
        },
        column_order=(display_columns),
        hide_index=True,
        use_container_width=True,
    )

    # Defenders points projections visualization
    st.header("Defenders")
    st.dataframe(
        defenders_df.style.background_gradient(
            axis=0, subset=gameweek_columns, cmap="RdYlGn"
        )
        .background_gradient(axis=0, subset="now_cost", cmap="Blues")
        .format({"now_cost": "£{:.1f}m"}, precision=2),
        column_config={
            "web_name": "Player",
            "team_name": "Team",
            "now_cost": st.column_config.NumberColumn("Price", help="FPL Price"),
        },
        column_order=(display_columns),
        hide_index=True,
        use_container_width=True,
    )

    # Goalkeepers points projections visualization
    st.header("Goalkeepers")
    st.dataframe(
        goalkeepers_df.style.background_gradient(
            axis=0, subset=gameweek_columns, cmap="RdYlGn"
        )
        .background_gradient(axis=0, subset="now_cost", cmap="Blues")
        .format({"now_cost": "£{:.1f}m"}, precision=2),
        column_config={
            "web_name": "Player",
            "team_name": "Team",
            "now_cost": st.column_config.NumberColumn("Price", help="FPL Price"),
        },
        column_order=(display_columns),
        hide_index=True,
        use_container_width=True,
    )

with combine_tab:
    # all players points projections visualization
    st.header("All Players")
    st.dataframe(
        projections_df.style.background_gradient(
            axis=0, subset=gameweek_columns, cmap="RdYlGn"
        )
        .background_gradient(axis=0, subset="now_cost", cmap="Blues")
        .format({"now_cost": "£{:.1f}m"}, precision=2),
        column_config={
            "web_name": "Player",
            "team_name": "Team",
            "now_cost": st.column_config.NumberColumn("Price", help="FPL Price"),
        },
        column_order=(display_columns),
        hide_index=True,
        use_container_width=True,
    )