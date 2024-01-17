import streamlit as st
import pandas as pd
import altair as alt

# read data in
player_data = pd.read_csv("data/2023/player_data.csv")
odm_data = pd.read_csv("data/2023/odm_rating.csv")
odm_data = odm_data.tail(20)

# page config
st.set_page_config(
    page_title="Player Comparison • FPLalytics", page_icon=":chart_with_upwards_trend:"
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
st.title("Player Comparison")
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to compare the performance and auxillary statistics of players.

Input data can be selected from the past six gameweeks or over the full season. The "Past 6 Gameweeks" option can be a better indicator of current form, but is more sensitive to outliers and variance.

Performance statistics can be displayed as totals or per 90 minutes."""
    )

# options
with st.expander("Options", expanded=False):
    # multiselect for player filter
    player_filter = st.multiselect(
        "Players",
        player_data["player"].unique(),
        default=["Erling Haaland", "Mohamed Salah", "Son Heung-Min"],
    )

    # Model select box
    model_option = st.selectbox("Data Source", ("Full Season", "Past 6 Gameweeks"))
    if model_option == "Past 6 Gameweeks":
        player_data = player_data[
            player_data["gameweek"] > (player_data["gameweek"].max() - 6)
        ]

    # checkbox to select per 90 stats
    per_90 = st.checkbox("Per 90 min stats", value=True)

# setup performance dataframe
player_data = player_data[player_data["player"].isin(player_filter)]
perf_df = player_data.groupby(["player"], as_index=False)[
    ["xGI", "goals", "xG", "shots", "assists", "xA", "key_passes", "time", "team_xG"]
].sum()
perf_df["t_score"] = (perf_df["xGI"] / perf_df["team_xG"]) * 100
if per_90:
    perf_df["xGI"] = perf_df["xGI"] / perf_df["time"] * 90
    perf_df["goals"] = perf_df["goals"] / perf_df["time"] * 90
    perf_df["xG"] = perf_df["xG"] / perf_df["time"] * 90
    perf_df["shots"] = perf_df["shots"] / perf_df["time"] * 90
    perf_df["assists"] = perf_df["assists"] / perf_df["time"] * 90
    perf_df["xA"] = perf_df["xA"] / perf_df["time"] * 90
    perf_df["key_passes"] = perf_df["key_passes"] / perf_df["time"] * 90

# setup auxillary dataframe
aux_df = (
    player_data.groupby(["player", "team_name"], as_index=False)
    .agg(
        minutes=("time", "sum"),
        appearances=("player", "count"),
        yc=("yellow_card", "sum"),
        rc=("red_card", "sum"),
    )
    .rename(columns={"team_name": "team"})
)
aux_df["mpa"] = aux_df["minutes"] / aux_df["appearances"]
if model_option == "Past 6 Gameweeks":
    aux_df = aux_df.merge(
        odm_data[["team", "o_rating_psix", "d_rating_psix"]], on="team"
    )
    aux_df = aux_df.rename(
        columns={"o_rating_psix": "o_rating", "d_rating_psix": "d_rating"}
    )
elif model_option == "Full Season":
    aux_df = aux_df.merge(
        odm_data[["team", "o_rating_season", "d_rating_season"]], on="team"
    )
    aux_df = aux_df.rename(
        columns={"o_rating_season": "o_rating", "d_rating_season": "d_rating"}
    )

# performance dataframe
st.markdown("### Performance Stats")
st.dataframe(
    perf_df.style.background_gradient(
        axis=0,
        subset=[
            "xGI",
            "goals",
            "xG",
            "shots",
            "assists",
            "xA",
            "key_passes",
            "t_score",
        ],
        cmap="Blues",
    ).format({"t_score": "{:.2f} %", "xG_perc": "{:.2f} %"}, precision=2),
    column_config={
        "player": "Player",
        "xGI": st.column_config.NumberColumn(
            "xGI", help="Expected Goal Involvement: xG + xA"
        ),
        "t_score": st.column_config.NumberColumn(
            "T-Score", help="Talisman Score: Player xGI as % of Team xG"
        ),
        "goals": "Goals",
        "shots": "Shots",
        "assists": "Assists",
        "key_passes": st.column_config.NumberColumn("KP", help="Key Passes"),
    },
    column_order=(
        "player",
        "xGI",
        "goals",
        "xG",
        "shots",
        "assists",
        "xA",
        "key_passes",
        "t_score",
    ),
    hide_index=True,
    use_container_width=True,
)

# auxillary stats dataframe
st.markdown("### Auxillary Stats")
st.dataframe(
    aux_df.style.background_gradient(axis=0, subset=["o_rating"], cmap="Blues")
    .background_gradient(axis=0, subset=["d_rating"], cmap="Blues_r")
    .format(
        {
            "o_rating": "{:1.0f}",
            "mpa": "{:1.0f}",
        },
        precision=2,
    ),
    column_config={
        "player": "Player",
        "team": "Team",
        "minutes": "Minutes",
        "appearances": "Appearances",
        "mpa": st.column_config.NumberColumn("MPA", help="Minutes Per Appearance"),
        "yc": st.column_config.NumberColumn("YC", help="Yellow Cards"),
        "rc": st.column_config.NumberColumn("RC", help="Red Cards"),
        "o_rating": st.column_config.NumberColumn(
            "Offense", help="Team Offense Rating from ODM model"
        ),
        "d_rating": st.column_config.NumberColumn(
            "Defense", help="Team Defense Rating from ODM model"
        ),
    },
    column_order=(
        "player",
        "team",
        "o_rating",
        "d_rating",
        "appearances",
        "minutes",
        "mpa",
        "yc",
        "rc",
    ),
    hide_index=True,
    use_container_width=True,
)
