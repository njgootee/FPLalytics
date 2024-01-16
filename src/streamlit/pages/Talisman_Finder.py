import streamlit as st
import pandas as pd
import altair as alt

# read data in
player_data = pd.read_csv("../../data/2023/player_data.csv")

# page config
st.set_page_config(
    page_title="Talisman Finder • FPLalytics", page_icon=":chart_with_upwards_trend:"
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
        """Use this tool to identify the top five talismans for each team. 
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
    team_filter = st.selectbox("Team", sorted(player_data["team_name"].unique()))

# setup df
player_data = player_data[player_data["team_name"] == team_filter]
if model_option == "Past 6 Gameweeks":
    player_data = player_data[
        player_data["gameweek"] > (player_data["gameweek"].max() - 6)
    ]
chart_df = player_data.groupby(["player"], as_index=False)[
    ["xGI", "team_xG", "xG", "xA", "time"]
].sum()
chart_df["t_score"] = (chart_df["xGI"] / chart_df["team_xG"]) * 100
chart_df["xG_perc"] = (chart_df["xG"] / chart_df["xGI"]) * 100
chart_df = chart_df.nlargest(5, "t_score")

# Talisman chart
tman_chart = (
    alt.Chart(chart_df)
    .mark_point()
    .encode(
        x=alt.X("team_xG", type="quantitative", title="Team xG"),
        y=alt.Y("t_score", type="quantitative", title="Talisman Score"),
        color=alt.Color("xG_perc:Q", title="xG%", scale=alt.Scale(scheme="blues")),
        tooltip=[
            alt.Tooltip("player", title="Player"),
            alt.Tooltip("t_score", title="Talisman Score", format=".2f"),
            alt.Tooltip("team_xG", title="Team xG", format=".2f"),
            alt.Tooltip("xG_perc", title="xG%", format=".2f"),
        ],
    )
)
st.altair_chart(tman_chart, use_container_width=True)

# Talisman table
st.dataframe(
    chart_df.style.background_gradient(axis=0, subset=["t_score"], cmap="Blues").format(
        {
            "t_score": "{:.2f} %",
            "xG_perc": "{:.2f} %",
        },
        precision=2,
    ),
    column_config={
        "player": "Player",
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
        "player",
        "team_name",
        "t_score",
        "xGI",
        "team_xG",
        "xG_perc",
        "xG",
        "xA",
        "time",
    ),
    hide_index=True,
    use_container_width=True,
)
