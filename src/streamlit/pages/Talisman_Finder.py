import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

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
    st.caption(
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
        """Use this tool to identify the top talismanic players of each team. 
A talisman is defined as a player with high percentage involvement in the attacking output of their team. This is measuredin the form of npxGI (non-penalty expected goal involvement). 

When searching for talismanic players, additional factors should be considered:
- Goal threat bias (percentage of npxGI coming from npxG rather than xA) to maximize expected FPL points
- Penalty takers for an extra route to FPL points

Use the options section to manipulate the source data.
* A smaller gameweek range can be a better indicator of form, but is more sensitive to outliers and variance (luck)

Note that team xG data for each player is only recorded when the player makes an appearance. This is why values for Team xG will vary for players on the same team.
"""
    )

# options
with st.expander("Options", expanded=False):
    # multiselect for team filter
    team_filter = st.selectbox(
        "Team", sorted(np.append(player_data["team_name"].unique(), ["All"]))
    )
    if team_filter != "All":
        player_data = player_data[player_data["team_name"] == team_filter]

    # select gameweek range
    gw_option = st.slider("Gameweek Range", 1, latest_gw, (1, latest_gw))
    # filter by gameweeks
    player_data = player_data[
        (player_data["gameweek"] >= gw_option[0])
        & (player_data["gameweek"] <= gw_option[1])
    ]

    # groupby dataframe
    chart_df = player_data.groupby(["player_id"], as_index=False)[
        ["npxGI", "team_xG", "npxG", "xA", "time"]
    ].sum()

    # slider for minutes played
    minutes_option = st.slider(
        "Minimum Minutes Played",
        1,
        latest_gw * 90,
        min([(gw_option[1] - gw_option[0] + 1) * 45, 180]),
    )
    chart_df = chart_df[chart_df["time"] >= minutes_option]

    # checkbox for detailed stats
    detail_option = st.checkbox("Display Detailed Stats", value=False)
    if detail_option:
        table_columns = [
            "web_name_pos",
            "t_score",
            "xG_perc",
            "penalties_order",
            "time",
            "npxGI",
            "team_xG",
        ]
    else:
        table_columns = ["web_name_pos", "t_score", "xG_perc", "penalties_order"]

# setup dataframe
chart_df["t_score"] = (chart_df["npxGI"] / chart_df["team_xG"]) * 100
chart_df["xG_perc"] = (chart_df["npxG"] / chart_df["npxGI"]) * 100
chart_df = chart_df[chart_df["t_score"] > 0].sort_values("t_score", ascending=False)

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
    talisman_df = st.dataframe(
        chart_df.style.background_gradient(
            axis=0, subset=["t_score", "xG_perc"], cmap="Blues"
        ).highlight_between(subset="penalties_order", color="#60B4FF", right=1)
        .format(
            {"t_score": "{:.0f} %", "xG_perc": "{:.0f} %", "penalties_order": "{:.0f}"},
            precision=0,
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
        column_order=(table_columns),
        hide_index=True,
        on_select="rerun",
        use_container_width=True,
        height=525,
    )

    # user player higlight selection
    selected_players = talisman_df.selection.rows
    selected_player_id = chart_df.iloc[selected_players]["player_id"].to_list()

# Talisman chart
with col2:
    tman_chart = (
        alt.Chart(chart_df)
        .mark_point(filled=True, size=100)
        .encode(
            x=alt.X(
                "xG_perc",
                type="quantitative",
                title="Goal Threat Bias (%)",
                scale=alt.Scale(domain=[0, 100]),
            ),
            y=alt.Y(
                "t_score",
                type="quantitative",
                title="Talisman Score (%)",
                scale=alt.Scale(domain=[0, 100]),
            ),
            color=alt.condition(
                alt.FieldOneOfPredicate(field="player_id", oneOf=selected_player_id),
                if_true=alt.value("#FFE261"),
                if_false=alt.Color(
                    "time:Q",
                    title="Minutes",
                    scale=alt.Scale(
                        scheme="blues",
                        domain=[0, (gw_option[1] - gw_option[0] + 1) * 90],
                    ),
                ),
            ),
            tooltip=[
                alt.Tooltip("web_name_pos", title="Player"),
                alt.Tooltip("t_score", title="Talisman Score", format=".0f"),
                alt.Tooltip("xG_perc", title="Goal Threat Bias", format=".0f"),
                alt.Tooltip("time", title="Minutes", format=".0f"),
                alt.Tooltip("penalties_order", title="Penalty Order"),
            ],
            shape=alt.Shape("penalties_order:O", legend=None).scale(
                range=["circle", "cross", "circle", "circle"]
            ),
        )
        .properties(height=600)
    )

    # Highlighted players text
    text = (
        alt.Chart(chart_df[chart_df["player_id"].isin(selected_player_id)])
        .mark_text(color="#FFE261", align="center", dy=-10)
        .encode(
            x="xG_perc",
            y="t_score",
            text="web_name_pos",
            tooltip=alt.value(None),
        )
    )
    st.altair_chart(tman_chart + text, use_container_width=True)
