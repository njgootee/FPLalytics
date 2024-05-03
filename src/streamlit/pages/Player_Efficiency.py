import streamlit as st
import pandas as pd
import matplotlib

# read data in
player_data = pd.read_csv("data/2023/player_data.csv")
player_mapping = pd.read_csv("data/2023/player_mapping.csv")

# add fpl info
player_mapping = player_mapping.dropna()
player_mapping["web_name_pos"] = (
    player_mapping["web_name"] + " " + player_mapping["pos"]
)
player_data = player_data.merge(
    player_mapping[["player_id", "web_name_pos"]], how="left", on="player_id"
)
player_data = player_data.dropna(subset="web_name_pos")

# page config
st.set_page_config(
    page_title="Player Efficiency • FPLalytics",
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
st.title("Player Efficiency")
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to compare the goal and assist efficiency of players. 
Efficiency is defined as the difference between xG/xA and goals/assists respectively. 
A high efficiency could indicate a player with above average finishing ability (or assisting players with above average finishing ability), whereas a low efficiency could indicate the opposite.

Input data can be selected from the past six gameweeks or over the full season. The "Past 6 Gameweeks" option can be a better indicator of current form, but is more sensitive to outliers and variance."""
    )

# options
with st.expander("Options", expanded=False):
    # Model select box
    model_option = st.selectbox("Data source", ("Full Season", "Past 6 Gameweeks"))
    if model_option == "Past 6 Gameweeks":
        player_data = player_data[
            player_data["gameweek"] > (player_data["gameweek"].max() - 6)
        ]

    # slider to select top/bottom n results
    n_players = st.slider("Max number of players displayed", 5, 20, 10)

    # slider to set quantile
    quantile = st.slider("Quantile for xG / xA", 0.75, 0.99, 0.90)

    # set up chart dataframe
    chart_df = player_data.groupby(["web_name_pos"], as_index=False)[
        ["xG", "goals", "xA", "assists"]
    ].sum()
    chart_df["xG_difference"] = chart_df["goals"] - chart_df["xG"]
    chart_df["xA_difference"] = chart_df["assists"] - chart_df["xA"]

    # Quantile caption
    st.caption(
        "Filtered to: xG ≥ "
        + str(chart_df["xG"].quantile(q=quantile).round(2))
        + ", xA ≥ "
        + str(chart_df["xA"].quantile(q=quantile).round(2))
    )

# tabs
g_tab, a_tab = st.tabs(["Goals", "Assists"])

# goals
with g_tab:
    col1, col2 = st.columns(2)
    # strong finishers
    with col1:
        st.markdown("High Goal Efficiency")
        st.dataframe(
            chart_df[
                (chart_df["xG"] >= chart_df["xG"].quantile(q=quantile))
                & (chart_df["xG_difference"] > 0)
            ]
            .nlargest(n_players, "xG_difference")
            .style.background_gradient(axis=0, subset=["xG_difference"], cmap="Blues")
            .format(precision=2),
            column_config={
                "web_name_pos": "Player",
                "goals": "Goals",
                "xG_difference": st.column_config.NumberColumn(
                    "Difference",
                    help="Goals - xG",
                ),
            },
            column_order=("web_name_pos", "goals", "xG", "xG_difference"),
            hide_index=True,
            use_container_width=True,
        )

    # poor finishers
    with col2:
        st.markdown("Low Goal Efficiency")
        st.dataframe(
            chart_df[
                (chart_df["xG"] >= chart_df["xG"].quantile(q=quantile))
                & (chart_df["xG_difference"] < 0)
            ]
            .nsmallest(n_players, "xG_difference")
            .style.background_gradient(axis=0, subset=["xG_difference"], cmap="Reds_r")
            .format(precision=2),
            column_config={
                "web_name_pos": "Player",
                "goals": "Goals",
                "xG_difference": st.column_config.NumberColumn(
                    "Difference",
                    help="Goals - xG",
                ),
            },
            column_order=("web_name_pos", "goals", "xG", "xG_difference"),
            hide_index=True,
            use_container_width=True,
        )

# assists
with a_tab:
    col1, col2 = st.columns(2)
    # strong assisters
    with col1:
        st.markdown("High Assist Efficiency")
        st.dataframe(
            chart_df[
                (chart_df["xA"] >= chart_df["xA"].quantile(q=quantile))
                & (chart_df["xA_difference"] > 0)
            ]
            .nlargest(n_players, "xA_difference")
            .style.background_gradient(axis=0, subset=["xA_difference"], cmap="Blues")
            .format(precision=2),
            column_config={
                "web_name_pos": "Player",
                "assists": "Assists",
                "xA_difference": st.column_config.NumberColumn(
                    "Difference",
                    help="Assists - xA",
                ),
            },
            column_order=("web_name_pos", "assists", "xA", "xA_difference"),
            hide_index=True,
            use_container_width=True,
        )

    # poor assisters
    with col2:
        st.markdown("Low Assist Efficiency")
        st.dataframe(
            chart_df[
                (chart_df["xA"] >= chart_df["xA"].quantile(q=quantile))
                & (chart_df["xA_difference"] < 0)
            ]
            .nsmallest(n_players, "xA_difference")
            .style.background_gradient(axis=0, subset=["xA_difference"], cmap="Reds_r")
            .format(precision=2),
            column_config={
                "web_name_pos": "Player",
                "assists": "Assists",
                "xA_difference": st.column_config.NumberColumn(
                    "Difference",
                    help="Assists - xA",
                ),
            },
            column_order=("web_name_pos", "assists", "xA", "xA_difference"),
            hide_index=True,
            use_container_width=True,
        )
