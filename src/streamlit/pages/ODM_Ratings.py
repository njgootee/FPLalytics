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
team_mapping = pd.read_csv("data/" + str(season_option)[:4] + "/team_mapping.csv")
odm_data = odm_data.merge(team_mapping, how="left", on="team_id")

# calculate overall rankings
odm_data["ovr_rating_season"] = (
    odm_data["o_rating_season"] / odm_data["d_rating_season"]
)
odm_data["ovr_rating_psix"] = odm_data["o_rating_psix"] / odm_data["d_rating_psix"]

# title and information
st.title("Offensive / Defensive Ratings")
if latest_gw < 7:
    st.caption(
        ":warning: Early Season View",
        help="ODM ratings are based on past season until Gameweek 7",
    )
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


# Team on-click highlight
context_selection = alt.selection_point(fields=["team"])

# tabs
od_tab, ovr_tab = st.tabs(["Offense/Defense", "Overall"])

# offense/defense tab
with od_tab:
    col1, col2 = st.columns(2)
    # Offensive rating chart
    with col1:
        st.header("Offensive Ratings")
        st.caption("Greater value indicates stronger offense")
        off_chart = (
            alt.Chart(odm_data, height=600)
            .mark_bar()
            .encode(
                x=alt.X(
                    "o_rating_" + model_type,
                    type="quantitative",
                    title="Offensive Rating",
                ),
                y=alt.Y("team_short", type="nominal", title="").sort("-x"),
                color=alt.condition(
                    context_selection, alt.value("#ff4b4b"), alt.value("#262730")
                ),
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
        st.caption("Lesser value indicates stronger defense")
        def_chart = (
            alt.Chart(odm_data, height=600)
            .mark_bar()
            .encode(
                x=alt.X(
                    "d_rating_" + model_type,
                    type="quantitative",
                    title="Defensive Rating",
                ),
                y=alt.Y("team_short", type="nominal", title="").sort("x"),
                color=alt.condition(
                    context_selection, alt.value("#60b4ff"), alt.value("#262730")
                ),
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

# overall tab
with ovr_tab:
    col1, col2 = st.columns(2)
    with col1:
        # offense vs defense scatter chart
        st.header("Offense vs Defense")
        st.caption("Compare offensive and defensive strength")
        scatter_chart = (
            alt.Chart(odm_data, height=600)
            .mark_point()
            .encode(
                x=alt.X(
                    "d_rating_" + model_type,
                    type="quantitative",
                    title="Defensive Rating",
                ),
                y=alt.Y(
                    "o_rating_" + model_type,
                    type="quantitative",
                    title="Offensive Rating",
                ),
                tooltip=[
                    alt.Tooltip("team_name", title="Team"),
                    alt.Tooltip(
                        "o_rating_" + model_type, title="Offensive Rating", format="d"
                    ),
                    alt.Tooltip(
                        "d_rating_" + model_type, title="Defensive Rating", format=".2f"
                    ),
                ],
                color=alt.Color("team_name", legend=None),
            )
            .configure_range(
                category=alt.RangeScheme(odm_data["team_colour"].to_list())
            )
        )
        st.altair_chart(scatter_chart, use_container_width=True)

    with col2:
        # Overall rating chart
        st.header("Overall Ratings")
        st.caption("Greater value indicates stronger overall")
        ovr_chart = (
            alt.Chart(odm_data, height=600)
            .mark_bar()
            .encode(
                x=alt.X(
                    "ovr_rating_" + model_type,
                    type="quantitative",
                    title="Offensive Rating",
                ),
                y=alt.Y("team_short", type="nominal", title="").sort("-x"),
                color=alt.condition(
                    context_selection, alt.value("#8B61FF"), alt.value("#262730")
                ),
                tooltip=[
                    alt.Tooltip("team", title="Team"),
                    alt.Tooltip(
                        "ovr_rating_" + model_type,
                        title="Overall Rating",
                        type="quantitative",
                        format="d",
                    ),
                ],
            )
            .add_params(context_selection)
        )
        st.altair_chart(ovr_chart, use_container_width=True)
