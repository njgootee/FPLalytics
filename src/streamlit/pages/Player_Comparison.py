import streamlit as st
import pandas as pd

# read app vars in
app_vars = pd.read_csv("data/app_vars.csv")
seasons = app_vars["season"]

# page config
st.set_page_config(
    page_title="Player Comparison • FPLalytics",
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
odm_data = pd.read_csv("data/" + str(season_option)[:4] + "/odm_rating.csv")
odm_data = odm_data.tail(20)

# title and information
st.title("Player Comparison")
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to compare the performance and auxillary statistics of players.

Input data can be selected from the past six gameweeks or over the full season. The "Past 6 Gameweeks" option can be a better indicator of current form, but is more sensitive to outliers and variance.

Performance statistics can be displayed as totals or per 90 minutes."""
    )

# add fpl info
player_mapping = player_mapping.dropna(subset="fpl_id")
player_mapping["web_name_pos"] = (
    player_mapping["web_name"] + " " + player_mapping["pos"]
)
player_data = player_data.merge(
    player_mapping[["player_id", "web_name_pos"]], how="left", on="player_id"
)
player_data = player_data.dropna(subset="web_name_pos")

# options
with st.expander("Options", expanded=False):
    # multiselect for player filter
    player_filter = st.multiselect(
        "Players",
        player_data["player_id"].unique(),
        format_func=lambda x: player_data[player_data["player_id"] == x][
            "web_name_pos"
        ].values[-1]
        + " ["
        + player_data[player_data["player_id"] == x]["team_name"].values[-1]
        + "]",
        default=[8260, 1250, 8497],
    )

    # Model select box
    model_option = st.selectbox("Data Source", ("Full Season", "Past 6 Gameweeks"))
    if model_option == "Past 6 Gameweeks":
        player_data = player_data[
            player_data["gameweek"] > (player_data["gameweek"].max() - 6)
        ]

    # checkbox to select per 90 stats
    per_90 = st.checkbox("Per 90 min stats", value=True)

    # checkbox to includ non-penalty data
    incl_np = st.checkbox("Display Non-Penalty xG", value=False)

# setup performance dataframe
player_data = player_data[player_data["player_id"].isin(player_filter)]
player_data["GI"] = player_data["goals"] + player_data["assists"]
perf_df = player_data.groupby(["web_name_pos"], as_index=False)[
    [
        "GI",
        "xGI",
        "npxGI",
        "goals",
        "xG",
        "npxG",
        "shots",
        "assists",
        "xA",
        "key_passes",
        "time",
        "team_xG",
    ]
].sum()

perf_df["t_score"] = (perf_df["xGI"] / perf_df["team_xG"]) * 100

if per_90:
    perf_df["GI"] = perf_df["GI"] / perf_df["time"] * 90
    perf_df["xGI"] = perf_df["xGI"] / perf_df["time"] * 90
    perf_df["npxGI"] = perf_df["npxGI"] / perf_df["time"] * 90
    perf_df["goals"] = perf_df["goals"] / perf_df["time"] * 90
    perf_df["xG"] = perf_df["xG"] / perf_df["time"] * 90
    perf_df["npxG"] = perf_df["npxG"] / perf_df["time"] * 90
    perf_df["shots"] = perf_df["shots"] / perf_df["time"] * 90
    perf_df["assists"] = perf_df["assists"] / perf_df["time"] * 90
    perf_df["xA"] = perf_df["xA"] / perf_df["time"] * 90
    perf_df["key_passes"] = perf_df["key_passes"] / perf_df["time"] * 90

if incl_np:
    perf_df_columns = [
        "web_name_pos",
        "GI",
        "xGI",
        "npxGI",
        "t_score",
        "goals",
        "xG",
        "npxG",
        "shots",
        "assists",
        "xA",
        "key_passes",
    ]
else:
    perf_df_columns = [
        "web_name_pos",
        "GI",
        "xGI",
        "t_score",
        "goals",
        "xG",
        "shots",
        "assists",
        "xA",
        "key_passes",
    ]

# setup auxillary dataframe
aux_df = (
    player_data.groupby(["web_name_pos", "team_name"], as_index=False)
    .agg(
        minutes=("time", "sum"),
        appearances=("web_name_pos", "count"),
        yc=("yellow_card", "sum"),
        rc=("red_card", "sum"),
        penalties=("penalty", "sum"),
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
            "GI",
            "xGI",
            "npxGI",
            "t_score",
        ],
        cmap="Blues",
    )
    .background_gradient(
        axis=0,
        subset=["goals", "xG", "npxG", "shots", "assists", "xA", "key_passes"],
        cmap="Purples",
    )
    .background_gradient(
        axis=0,
        subset=["assists", "xA", "key_passes"],
        cmap="Reds",
    )
    .format({"t_score": "{:.2f} %", "xG_perc": "{:.2f} %"}, precision=2),
    column_config={
        "web_name_pos": "Player",
        "xGI": st.column_config.NumberColumn(
            "xGI", help="Expected Goal Involvement: xG + xA"
        ),
        "npxGI": st.column_config.NumberColumn(
            "npxGI", help="Non-Penalty Expected Goal Involvement: npxG + xA"
        ),
        "t_score": st.column_config.NumberColumn(
            "T-Score", help="Talisman Score: Player xGI as % of Team xG"
        ),
        "goals": "Goals",
        "xG": st.column_config.NumberColumn("xG", help="Expected Goals"),
        "npxG": st.column_config.NumberColumn(
            "npxG", help="Non-Penalty Expected Goals"
        ),
        "shots": "Shots",
        "assists": "Assists",
        "xA": st.column_config.NumberColumn("xA", help="Expected Assists"),
        "key_passes": st.column_config.NumberColumn("KP", help="Key Passes"),
    },
    column_order=(perf_df_columns),
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
        "web_name_pos": "Player",
        "team": "Team",
        "minutes": "Minutes",
        "appearances": "Appearances",
        "mpa": st.column_config.NumberColumn("MPA", help="Minutes Per Appearance"),
        "penalties": "Penalties",
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
        "web_name_pos",
        "team",
        "o_rating",
        "d_rating",
        "appearances",
        "minutes",
        "mpa",
        "penalties",
        "yc",
        "rc",
    ),
    hide_index=True,
    use_container_width=True,
)
