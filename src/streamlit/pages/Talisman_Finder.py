import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import matplotlib

# read data in
player_data = pd.read_csv("data/2023/player_data.csv")
player_mapping = pd.read_csv("data/2023/player_mapping.csv")

# add fpl info
player_mapping = player_mapping.dropna(subset="fpl_id")
player_mapping["web_name_pos"] = (
    player_mapping["web_name"] + " " + player_mapping["pos"]
)
player_data = player_data.merge(
    player_mapping[["player_id", "web_name_pos"]], how="left", on="player_id"
)
player_data = player_data.dropna(subset="web_name_pos")

# page config
st.set_page_config(
    page_title="Talisman Finder • FPLalytics",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

# sidebar
with st.sidebar:
    st.markdown(
        """:chart_with_upwards_trend: :blue[FPL]*alytics*  
                Latest gameweek data: :blue["""
        + str(player_data["gameweek"].max())
        + """]  
                [GitHub](https://github.com/njgootee)"""
    )

# title and information
st.title("Talisman Finder")
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to identify the top talismans for each team. 
A talisman is defined as a player with high involvement in the attacking output of their team, in the form of xGI (expected goal involvement). 

Team xG data for each player is only recorded when the player makes an appearance. This is why values for Team xG will vary for players on the same team.

Input data can be selected from the past six gameweeks or over the full season. The "Past 6 Gameweeks" option can be a better indicator of current form, but is more sensitive to outliers and variance.
"""
    )

# options
with st.expander("Options", expanded=False):
    # Model select box
    model_option = st.selectbox("Data Source", ("Full Season", "Past 6 Gameweeks"))

    # multiselect for team filter
    team_filter = st.selectbox("Team", sorted(np.append(player_data["team_name"].unique(), ["All"])))

# setup df
if team_filter != "All":
    player_data = player_data[player_data["team_name"] == team_filter]
if model_option == "Past 6 Gameweeks":
    player_data = player_data[
        player_data["gameweek"] > (player_data["gameweek"].max() - 6)
    ]
chart_df = player_data.groupby(["web_name_pos"], as_index=False)[
    ["xGI", "team_xG", "xG", "xA", "time"]
].sum()
chart_df["t_score"] = (chart_df["xGI"] / chart_df["team_xG"]) * 100
chart_df["xG_perc"] = (chart_df["xG"] / chart_df["xGI"]) * 100
chart_df = chart_df.nlargest(11, "t_score")

col1, col2 = st.columns(2)

# Talisman table
with col1:
    st.dataframe(
        chart_df.style.background_gradient(
            axis=0, subset=["t_score"], cmap="Blues"
        ).format(
            {
                "t_score": "{:.2f} %",
                "xG_perc": "{:.2f} %",
            },
            precision=2,
        ),
        column_config={
            "web_name_pos": "Player",
            "team_name": "Team",
            "t_score": st.column_config.NumberColumn(
                "Talisman Score",
                help="Player xGI as % of Team xG",
            ),
            "xGI": st.column_config.NumberColumn(
                "xGI",
                help="Expected Goal Involvement: xG + xA",
            ),
            "xG_perc": st.column_config.NumberColumn(
                "xG%",
                help="xG % of xGI",
            ),
            "team_xG": st.column_config.NumberColumn(
                "Team xG",
                help="Team total xG (when player makes appearance)",
            ),
            "time": "Minutes",
        },
        column_order=(
            "web_name_pos",
            "team_name",
            "t_score",
            "xGI",
            "team_xG",
            "xG_perc",
            "time",
        ),
        hide_index=True,
        use_container_width=True,
        height = 422
    )

# Talisman chart
with col2:
    tman_chart = (
        alt.Chart(chart_df)
        .mark_point()
        .encode(
            x=alt.X("xG_perc", type="quantitative", title="xG%"),
            y=alt.Y("t_score", type="quantitative", title="Talisman Score (%)"),
            color=alt.Color(
                "team_xG:Q", title="Team xG", scale=alt.Scale(scheme="blues")
            ),
            tooltip=[
                alt.Tooltip("web_name_pos", title="Player"),
                alt.Tooltip("t_score", title="Talisman Score", format=".2f"),
                alt.Tooltip("team_xG", title="Team xG", format=".2f"),
                alt.Tooltip("xG_perc", title="xG%", format=".2f"),
            ],
        )
        .properties(
            height=435
        )
    )
    st.altair_chart(tman_chart, use_container_width=True)