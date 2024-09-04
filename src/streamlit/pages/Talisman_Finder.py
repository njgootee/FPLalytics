import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import matplotlib

# read app vars in
app_vars = pd.read_csv("data/app_vars.csv")
seasons = app_vars["season"]

# page config
st.set_page_config(
    page_title="Talisman Finder • FPLalytics",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

# sidebar
with st.sidebar:
    st.markdown(""":chart_with_upwards_trend: :blue[FPL]*alytics*""")
    season_option = st.selectbox("Season", seasons)
    latest_gw = app_vars[app_vars["season"] == season_option]["latest_gameweek"].item()
    st.markdown(
        """Latest gameweek data: :blue["""
        + str(latest_gw)
        + """]  
                [GitHub](https://github.com/njgootee)"""
    )

# read data in
player_data = pd.read_csv("data/" + str(season_option)[:4] + "/player_data.csv")
player_mapping = pd.read_csv("data/" + str(season_option)[:4] + "/player_mapping.csv")

# title and information
st.title("Talisman Finder")
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to identify the top talismans for each team. 
A talisman is defined as a player with high involvement in the attacking output of their team, in the form of npxGI (non-penalty expected goal involvement). 

Team xG data for each player is only recorded when the player makes an appearance. This is why values for Team xG will vary for players on the same team.

Input data can be selected from the past six gameweeks or over the full season. The "Past 6 Gameweeks" option can be a better indicator of current form, but is more sensitive to outliers and variance.
"""
    )

# options
with st.expander("Options", expanded=False):
    # Model select box
    model_option = st.selectbox("Data Source", ("Full Season", "Past 6 Gameweeks"))
    if model_option == "Past 6 Gameweeks":
        player_data = player_data[
            player_data["gameweek"] > (player_data["gameweek"].max() - 6)
        ]

    # multiselect for team filter
    team_filter = st.selectbox(
        "Team", sorted(np.append(player_data["team_name"].unique(), ["All"]))
    )
    if team_filter != "All":
        player_data = player_data[player_data["team_name"] == team_filter]
    
    # groupby dataframe
    chart_df = player_data.groupby(["player_id"], as_index=False)[
        ["npxGI", "team_xG", "npxG", "xA", "time"]
    ].sum()

    # slider for minutes played
    minutes_option = st.slider("Minimum Minutes Played", 1, chart_df["time"].max(), 1)
    chart_df = chart_df[chart_df["time"]>=minutes_option]

    # checkbox for detailed stats
    detail_option = st.checkbox("Display Detailed Stats", value=False)
    if detail_option:
        table_columns = ["web_name_pos",
                "t_score",
                "xG_perc",
                "penalties_order",
                "time",
                "npxGI",
                "team_xG"]
    else:
        table_columns = ["web_name_pos",
                "t_score",
                "xG_perc",
                "penalties_order"]

# setup dataframe
chart_df["t_score"] = (chart_df["npxGI"] / chart_df["team_xG"]) * 100
chart_df["xG_perc"] = (chart_df["npxG"] / chart_df["npxGI"]) * 100
chart_df = chart_df[chart_df["t_score"]>0].sort_values("t_score", ascending = False)

# add fpl info
player_mapping = player_mapping.dropna(subset="fpl_id")
player_mapping["web_name_pos"] = (
    player_mapping["web_name"] + " " + player_mapping["pos"]
)
chart_df = chart_df.merge(
    player_mapping[["player_id", "web_name_pos", "penalties_order"]],
    how="left",
    on="player_id",
)
chart_df = chart_df.dropna(subset="web_name_pos")

col1, col2 = st.columns(2)

# Talisman table
with col1:
    st.dataframe(
        chart_df.style.background_gradient(
            axis=0, subset=["t_score", "xG_perc"], cmap="Blues"
        ).format(
            {
                "t_score": "{:.2f} %",
                "xG_perc": "{:.2f} %",
                "penalties_order": "{:.0f}"
            },
            precision=2,
        ),
        column_config={
            "web_name_pos": "Player",
            "t_score": st.column_config.NumberColumn(
                "Talisman Score",
                help="Player npxGI as % of Team xG",
            ),
            "npxGI": st.column_config.NumberColumn(
                "npxGI",
                help="Non-Penalty Expected Goal Involvement: npxG + xA",
            ),
            "xG_perc": st.column_config.NumberColumn(
                "Goal Threat Bias",
                help="npxG as % of npxGI",
            ),
            "team_xG": st.column_config.NumberColumn(
                "Team xG",
                help="Team total xG (when player makes appearance)",
            ),
            "time": st.column_config.NumberColumn(
                "Minutes",
                help="Minutes Played",
            ),
            "penalties_order": st.column_config.NumberColumn(
                "Penalty Order", help="Penalty Taker Order"
            ),
        },
        column_order=(
            table_columns
        ),
        hide_index=True,
        use_container_width=True,
        height=525,
    )

# Talisman chart
with col2:
    tman_chart = (
        alt.Chart(chart_df)
        .mark_point(filled = True, size = 100)
        .encode(
            x=alt.X("xG_perc", type="quantitative", title="Goal Threat Bias (%)", scale=alt.Scale(domain=[0,100])),
            y=alt.Y("t_score", type="quantitative", title="Talisman Score (%)", scale=alt.Scale(domain=[0,100])),
            color=alt.Color(
                "time:Q", title="Minutes", scale=alt.Scale(scheme="blues")
            ),
            tooltip=[
                alt.Tooltip("web_name_pos", title="Player"),
                alt.Tooltip("t_score", title="Talisman Score", format=".2f"),
                alt.Tooltip("xG_perc", title="Goal Threat Bias", format=".2f"),
                alt.Tooltip("time", title="Minutes", format=".0f"),
                alt.Tooltip("penalties_order", title="Penalty Order")
            ],
            shape = alt.Shape("penalties_order:O", legend=None).scale(range=["circle","cross","circle","circle"]),
        )
        .properties(height=600)
    )
    st.altair_chart(tman_chart, use_container_width=True)
