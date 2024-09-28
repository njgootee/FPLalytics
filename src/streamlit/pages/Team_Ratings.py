import streamlit as st
import pandas as pd
import altair as alt

# read app vars in
app_vars = pd.read_csv("data/app_vars.csv")
seasons = app_vars["season"]

# page config
st.set_page_config(
    page_title="Team Ratings • FPLalytics",
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
st.title("Team Offensive / Defensive Ratings")
if latest_gw < 7:
    st.caption(
        ":warning: Early Season View",
        help="ODM ratings are based on past season until Gameweek 7",
    )
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to compare relative overall, offensive, and defensive strength of teams.

Ratings are assigned based on the approach outlined in ["Offense-Defense Approach to Ranking Team Sports"](https://www.degruyter.com/document/doi/10.2202/1559-0410.1151/html), using xG as match scores (rather than goals).
A greater value in offensive rating indicates a stronger offense, whereas a stronger defense is indicated by a lesser value in defensive rating.
With xG as the algorithm input scores, offensive rating is representative of a teams ability to create goal scoring opportunities (in terms of quantity and quality).
Similarly, defensive rating is representative of a teams ability to limit their oppositions goal scoring opportunities.

Select input data with the options menu. The "Past 6 Gameweeks" option can be a better indicator of current form, but is more sensitive to outliers and variance.  
The dataframe and scatter plot are also interactive."""
    )

# options
with st.expander("Options", expanded=False):
    # Model select box
    model_option = st.selectbox("Data Source", ("Full Season", "Past 6 Gameweeks"))
    if model_option == "Full Season":
        model_type = "season"
    elif model_option == "Past 6 Gameweeks":
        model_type = "psix"

col1, col2 = st.columns(2)
with col1:
    # ratings dataframe
    rating_df = st.dataframe(
        odm_data.sort_values("ovr_rating_" + model_type, ascending=False),
        column_config={
            "team_short": "Team",
            "ovr_rating_"
            + model_type: st.column_config.ProgressColumn(
                "Overall Rating",
                help="= Offensive Rating / Defensive Rating",
                format="%d",
                max_value=odm_data["ovr_rating_" + model_type].max(),
            ),
            "o_rating_"
            + model_type: st.column_config.ProgressColumn(
                "Offensive Rating",
                help="Higher is better",
                format="%d",
                max_value=odm_data["o_rating_" + model_type].max(),
            ),
            "d_rating_"
            + model_type: st.column_config.ProgressColumn(
                "Defensive Rating",
                help="Lower is better",
                format="%.2f",
                max_value=odm_data["d_rating_" + model_type].max(),
            ),
        },
        column_order=(
            "team_short",
            "ovr_rating_" + model_type,
            "o_rating_" + model_type,
            "d_rating_" + model_type,
        ),
        hide_index=True,
        on_select="rerun",
        use_container_width=True,
        height=737,
    )

# identify selected teams to highlight
selected_team = rating_df.selection.rows
selected_team_id = (
    odm_data.sort_values("ovr_rating_" + model_type, ascending=False)
    .iloc[selected_team]["team_id"]
    .to_list()
)

with col2:
    # offense vs defense scatter plot
    scatter_plot = (
        alt.Chart(odm_data, height=750)
        .mark_point(filled=True, size=200)
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
                    "ovr_rating_" + model_type, title="Overall Rating", format="d"
                ),
                alt.Tooltip(
                    "o_rating_" + model_type, title="Offensive Rating", format="d"
                ),
                alt.Tooltip(
                    "d_rating_" + model_type, title="Defensive Rating", format=".2f"
                ),
            ],
            color=alt.Color("team_name", legend=None),
            opacity=alt.condition(
                (alt.FieldOneOfPredicate(field="team_id", oneOf=selected_team_id)),
                if_true=alt.value(1),
                if_false=alt.value(0.66),
            ),
        )
    )

    # mean offense line
    off_line = (
        alt.Chart(
            pd.DataFrame(
                {"Mean Offensive Rating": [odm_data["o_rating_" + model_type].mean()]}
            )
        )
        .mark_rule(color="#60b4ff", opacity=0.66)
        .encode(y="Mean Offensive Rating")
    )

    # mean defense line
    def_line = (
        alt.Chart(
            pd.DataFrame(
                {"Mean Defensive Rating": [odm_data["d_rating_" + model_type].mean()]}
            )
        )
        .mark_rule(color="#60b4ff", opacity=0.66)
        .encode(x="Mean Defensive Rating")
    )

    # Highlighted teams text
    highlight_text = (
        alt.Chart(odm_data[odm_data["team_id"].isin(selected_team_id)])
        .mark_text(
            align="center",
            dy=-12,
            color="#60b4ff",
            fontSize=12,
            fontWeight="bold",
            opacity=1,
        )
        .encode(
            x="d_rating_" + model_type,
            y="o_rating_" + model_type,
            text="team_short",
            tooltip=alt.value(None),
        )
    )

    # info text
    info_text1 = (
        alt.Chart(
            pd.DataFrame(
                {
                    "text": ["Strong Offense, Strong Defense"],
                    "x": [0],
                    "y": [odm_data["o_rating_" + model_type].max()],
                }
            )
        )
        .mark_text(
            align="left",
            dx=10,
            dy=-35,
            color="#60b4ff",
            opacity=0.5,
        )
        .encode(
            x="x",
            y="y",
            text="text",
            tooltip=alt.value(None),
        )
    )

    info_text2 = (
        alt.Chart(
            pd.DataFrame(
                {
                    "text": ["Strong Offense, Weak Defense"],
                    "x": [odm_data["d_rating_" + model_type].max()],
                    "y": [odm_data["o_rating_" + model_type].max()],
                }
            )
        )
        .mark_text(
            align="right",
            dx=10,
            dy=-35,
            color="#60b4ff",
            opacity=0.5,
        )
        .encode(
            x="x",
            y="y",
            text="text",
            tooltip=alt.value(None),
        )
    )

    info_text3 = (
        alt.Chart(
            pd.DataFrame({"text": ["Weak Offense, Strong Defense"], "x": [0], "y": [0]})
        )
        .mark_text(
            align="left",
            dx=10,
            dy=-10,
            color="#60b4ff",
            opacity=0.5,
        )
        .encode(
            x="x",
            y="y",
            text="text",
            tooltip=alt.value(None),
        )
    )

    info_text4 = (
        alt.Chart(
            pd.DataFrame(
                {
                    "text": ["Weak Offense, Weak Defense"],
                    "x": [odm_data["d_rating_" + model_type].max()],
                    "y": [0],
                }
            )
        )
        .mark_text(
            align="right",
            dx=10,
            dy=-10,
            color="#60b4ff",
            opacity=0.5,
        )
        .encode(
            x="x",
            y="y",
            text="text",
            tooltip=alt.value(None),
        )
    )

    # layer charts
    overall_chart = alt.layer(
        off_line,
        def_line,
        scatter_plot,
        highlight_text,
        info_text1,
        info_text2,
        info_text3,
        info_text4,
    ).configure_range(category=alt.RangeScheme(odm_data["team_colour"].to_list()))
    st.altair_chart(overall_chart, use_container_width=True)
