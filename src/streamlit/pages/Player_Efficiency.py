import streamlit as st
import pandas as pd
import altair as alt

# read app vars in
app_vars = pd.read_csv("data/app_vars.csv")
seasons = app_vars["season"]

# page config
st.set_page_config(
    page_title="Player Efficiency • FPLalytics",
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
st.title("Player Efficiency")
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to compare the goal and assist efficiency of players.
Efficiency is defined as the difference between xG and goals, or xA and assists. 
* At an efficiency of zero, a player is returning goals or assists in line with their xG or xA. 
* A high efficiency indicates a player with strong finishing ability, whereas a low efficiency indicates a poor finisher.
* In terms of assists, efficiency values relate to creating chances for players with strong or poor finishing ability.
* Keep in mind that (good or bad) luck can influence a players efficiency, but this noise is greatly diminished with larger sample sizes.

Use the options section to manipulate the source data.
* A smaller gameweek range can be a better indicator of form, but is more sensitive to outliers and variance (luck)

The data elements can also be interacted with.
* Search the dataframe and select players via the leftmost column to highlight their position in the adjacent scatter plot.
* Hover of scatterplot marks for detailed tooltip"""
    )

# options
with st.expander("Options", expanded=False):
    # select gameweek range
    gw_option = st.slider("Gameweek Range", 1, latest_gw, (1, latest_gw))
    # filter by gameweeks
    player_data = player_data[
        (player_data["gameweek"] >= gw_option[0])
        & (player_data["gameweek"] <= gw_option[1])
    ]

    # set up chart dataframe
    player_data["npgoals"] = player_data["goals"] - player_data["penalty_scored"]
    chart_df = player_data.groupby(["player_id"], as_index=False)[
        ["npxG", "npgoals", "xA", "assists", "time"]
    ].sum()
    chart_df["npxG_difference"] = chart_df["npgoals"] - chart_df["npxG"]
    chart_df["xA_difference"] = chart_df["assists"] - chart_df["xA"]

    # slider to select minimum minutes played
    minutes_option = st.slider(
        "Minimum Minutes Played",
        1,
        latest_gw * 90,
        min([(gw_option[1] - gw_option[0] + 1) * 45, 180]),
    )
    # filter by minimum minutes
    chart_df = chart_df[chart_df["time"] >= minutes_option]

    # checkbox to select per 90 stats
    per_90 = st.checkbox("Per 90 Min Stats", value=True)
    # adjust for per 90
    if per_90:
        chart_df["npxG_difference"] = (
            chart_df["npxG_difference"] / chart_df["time"] * 90
        )
        chart_df["npxG"] = chart_df["npxG"] / chart_df["time"] * 90
        chart_df["npgoals"] = chart_df["npgoals"] / chart_df["time"] * 90
        chart_df["xA_difference"] = chart_df["xA_difference"] / chart_df["time"] * 90
        chart_df["xA"] = chart_df["xA"] / chart_df["time"] * 90
        chart_df["assists"] = chart_df["assists"] / chart_df["time"] * 90

    # slider to set npxG / xA quantile
    quantile = st.slider("npxG / xA Quantile", 0.01, 0.99, 0.75)
    # quantile caption
    st.caption(
        "Filtered to: npxG ≥ "
        + str(chart_df["npxG"].quantile(q=quantile).round(2))
        + ", xA ≥ "
        + str(chart_df["xA"].quantile(q=quantile).round(2))
    )

# add fpl info to dataframe
player_mapping = player_mapping.dropna(subset="fpl_id")
player_mapping["web_name_pos"] = (
    player_mapping["web_name"] + " " + player_mapping["pos"]
)
chart_df = chart_df.merge(
    player_mapping[["player_id", "web_name_pos"]], how="left", on="player_id"
)
chart_df = chart_df.dropna(subset="web_name_pos")

# tabs
g_tab, a_tab = st.tabs(["Goals", "Assists"])

# goals tab
with g_tab:
    col1, col2 = st.columns(2)
    # dataframe
    with col1:
        goal_eff_df = st.dataframe(
            chart_df[(chart_df["npxG"] >= chart_df["npxG"].quantile(q=quantile))]
            .sort_values(by="npxG_difference", ascending=False)
            .style.background_gradient(
                axis=0, subset=["npxG_difference"], cmap="RdYlGn"
            )
            .format(precision=2),
            column_config={
                "web_name_pos": "Player",
                "npgoals": "Non-Penalty Goals",
                "npxG": st.column_config.NumberColumn(
                    "npxG",
                    help="Non-Penalty Expected Goals",
                ),
                "npxG_difference": st.column_config.NumberColumn(
                    "Efficiency",
                    help="npGoals - npxG",
                ),
            },
            column_order=("web_name_pos", "npgoals", "npxG", "npxG_difference"),
            hide_index=True,
            on_select="rerun",
            use_container_width=True,
            height=490,
        )

    # user player higlight selection
    selected_players = goal_eff_df.selection.rows
    selected_player_id = (
        chart_df[(chart_df["npxG"] >= chart_df["npxG"].quantile(q=quantile))]
        .sort_values(by="npxG_difference", ascending=False)
        .iloc[selected_players]["player_id"]
        .to_list()
    )

    # chart
    with col2:
        # scatter plot
        goal_eff_chart = (
            alt.Chart(
                chart_df[(chart_df["npxG"] >= chart_df["npxG"].quantile(q=quantile))]
            )
            .mark_point(filled=True, size=100)
            .encode(
                x=alt.X("npxG", type="quantitative", title="npxG"),
                y=alt.Y(
                    "npxG_difference",
                    type="quantitative",
                    title="Efficiency (npGoals - npxG)",
                ),
                tooltip=[
                    alt.Tooltip("web_name_pos", title="Player"),
                    alt.Tooltip("npxG_difference", title="Efficiency", format=".2f"),
                    alt.Tooltip("npgoals", title="Non-Penalty Goals", format=".2f"),
                    alt.Tooltip("npxG", title="npxG", format=".2f"),
                    alt.Tooltip("time", title="Minutes", format=".0f"),
                ],
                color=alt.condition(
                    alt.FieldOneOfPredicate(
                        field="player_id", oneOf=selected_player_id
                    ),
                    if_true=alt.value("#FFE261"),
                    if_false=alt.value("#60b4ff"),
                ),
            )
            .properties(height=565)
        )

        # Efficiency=0 line
        line = (
            alt.Chart(pd.DataFrame({"Efficiency": [0]}))
            .mark_rule(color="#ff4b4b")
            .encode(y="Efficiency")
        )

        # Highlighted players text
        text = (
            alt.Chart(chart_df[chart_df["player_id"].isin(selected_player_id)])
            .mark_text(color="#FFE261", align="center", dy=-10)
            .encode(x="npxG", y="npxG_difference", text="web_name_pos")
        )
        st.altair_chart(goal_eff_chart + line + text, use_container_width=True)

# assists
with a_tab:
    col1, col2 = st.columns(2)
    # dataframe
    with col1:
        assist_eff_df = st.dataframe(
            chart_df[(chart_df["xA"] >= chart_df["xA"].quantile(q=quantile))]
            .sort_values(by="xA_difference", ascending=False)
            .style.background_gradient(axis=0, subset=["xA_difference"], cmap="RdYlGn")
            .format(precision=2),
            column_config={
                "web_name_pos": "Player",
                "assists": "Assists",
                "xA": st.column_config.NumberColumn(
                    "xA",
                    help="Expected Assists",
                ),
                "xA_difference": st.column_config.NumberColumn(
                    "Efficiency",
                    help="Assists - xA",
                ),
            },
            column_order=("web_name_pos", "assists", "xA", "xA_difference"),
            hide_index=True,
            on_select="rerun",
            use_container_width=True,
            height=490,
        )

    # user player higlight selection
    selected_players = assist_eff_df.selection.rows
    selected_player_id = (
        chart_df[(chart_df["xA"] >= chart_df["xA"].quantile(q=quantile))]
        .sort_values(by="xA_difference", ascending=False)
        .iloc[selected_players]["player_id"]
        .to_list()
    )

    # chart
    with col2:
        # scatter plot
        assist_eff_chart = (
            alt.Chart(chart_df[(chart_df["xA"] >= chart_df["xA"].quantile(q=quantile))])
            .mark_point(filled=True, size=100)
            .encode(
                x=alt.X("xA", type="quantitative", title="xA"),
                y=alt.Y(
                    "xA_difference",
                    type="quantitative",
                    title="Efficiency (Assists - xA)",
                ),
                tooltip=[
                    alt.Tooltip("web_name_pos", title="Player"),
                    alt.Tooltip("xA_difference", title="Efficiency", format=".2f"),
                    alt.Tooltip("assists", title="Assists", format=".2f"),
                    alt.Tooltip("xA", title="xA", format=".2f"),
                    alt.Tooltip("time", title="Minutes", format=".0f"),
                ],
                color=alt.condition(
                    alt.FieldOneOfPredicate(
                        field="player_id", oneOf=selected_player_id
                    ),
                    if_true=alt.value("#FFE261"),
                    if_false=alt.value("#60b4ff"),
                ),
            )
            .properties(height=565)
        )

        # Efficiency=0 line
        line = (
            alt.Chart(pd.DataFrame({"Efficiency": [0]}))
            .mark_rule(color="#ff4b4b")
            .encode(y="Efficiency")
        )

        # Highlighted players text
        text = (
            alt.Chart(chart_df[chart_df["player_id"].isin(selected_player_id)])
            .mark_text(color="#FFE261", align="center", dy=-10)
            .encode(x="xA", y="xA_difference", text="web_name_pos")
        )
        st.altair_chart(assist_eff_chart + line + text, use_container_width=True)
