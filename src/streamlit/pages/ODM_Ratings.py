import streamlit as st
import pandas as pd
import altair as alt

# read app vars in
app_vars = pd.read_csv("data/app_vars.csv")
seasons = app_vars["season"]

# page config
st.set_page_config(
    page_title="ODM Ratings • FPLalytics",
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
odm_data = pd.read_csv("data/" + str(season_option)[:4] + "/odm_rating.csv")
odm_data = odm_data.tail(20)

# title and information
st.title("Offensive / Defensive Ratings")
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to compare offensive and defensive strength of teams.

Ratings are assigned based on the approach outlined in ["Offense-Defense Approach to Ranking Team Sports"](https://www.degruyter.com/document/doi/10.2202/1559-0410.1151/html), using xG as scores (rather than goals).
A greater value in offensive rating indicates a stronger offence, whereas a stronger defence is indicated by a lesser value in defensive rating.

Select input data with the options menu. The "Past 6 Gameweeks" option can be a better indicator of current form, but is more sensitive to outliers and variance."""
    )

with st.expander("Options", expanded=False):
    # Model select box
    model_option = st.selectbox("Data Source", ("Full Season", "Past 6 Gameweeks"))
    if model_option == "Full Season":
        model_type = "season"
    elif model_option == "Past 6 Gameweeks":
        model_type = "psix"

    # color type select box
    team_specific = st.checkbox("Use team specific color scheme")

# chart color mapping
domain = [
    "Arsenal",
    "Aston Villa",
    "Bournemouth",
    "Brentford",
    "Brighton",
    "Burnley",
    "Chelsea",
    "Crystal Palace",
    "Everton",
    "Fulham",
    "Liverpool",
    "Luton",
    "Manchester City",
    "Manchester United",
    "Newcastle United",
    "Nottingham Forest",
    "Sheffield United",
    "Tottenham",
    "West Ham",
    "Wolverhampton Wanderers",
]
range_ = [
    "#ff0000",
    "#490024",
    "#d71921",
    "#fd0000",
    "#0000fd",
    "#70193d",
    "#001489",
    "#0055a5",
    "#003399",
    "#ffffff",
    "#d3171e",
    "#fc5001",
    "#98c5e9",
    "#d20222",
    "#ffffff",
    "#dc0202",
    "#f12228",
    "#ffffff",
    "#540d1a",
    "#fc891c",
]

# Team highlight
context_selection = alt.selection_point(fields=["team"])
if team_specific:
    o_context_color = alt.condition(
        context_selection,
        alt.Color("team:N", scale=alt.Scale(domain=domain, range=range_), legend=None),
        alt.value("#262730"),
    )
    d_context_color = alt.condition(
        context_selection,
        alt.Color("team:N", scale=alt.Scale(domain=domain, range=range_), legend=None),
        alt.value("#262730"),
    )
else:
    o_context_color = alt.condition(
        context_selection, alt.value("#ff4b4b"), alt.value("#262730")
    )
    d_context_color = alt.condition(
        context_selection, alt.value("#60b4ff"), alt.value("#262730")
    )

col1, col2 = st.columns(2)
# Offensive rating chart
with col1:
    st.header("Offensive Ratings")
    off_chart = (
        alt.Chart(odm_data, height=600)
        .mark_bar()
        .encode(
            x=alt.X(
                "o_rating_" + model_type, type="quantitative", title="Offensive Rating"
            ),
            y=alt.Y("team", type="nominal", title="").sort("-x"),
            color=o_context_color,
            tooltip=[
                alt.Tooltip("team", title="Team"),
                alt.Tooltip(
                    "o_rating_" + model_type,
                    title="Offensive Rating",
                    type="quantitative",
                    format="d",
                ),
            ],
        )
        .add_params(context_selection)
    )
    st.altair_chart(off_chart, use_container_width=True)

# Defensive rating chart
with col2:
    st.header("Defensive Ratings")
    def_chart = (
        alt.Chart(odm_data, height=600)
        .mark_bar()
        .encode(
            x=alt.X(
                "d_rating_" + model_type, type="quantitative", title="Defensive Rating"
            ),
            y=alt.Y("team", type="nominal", title="").sort("x"),
            color=d_context_color,
            tooltip=[
                alt.Tooltip("team", title="Team"),
                alt.Tooltip(
                    "d_rating_" + model_type,
                    title="Defensive Rating",
                    type="quantitative",
                    format=".2f",
                ),
            ],
        )
        .add_params(context_selection)
    )
    st.altair_chart(def_chart, use_container_width=True)
