import streamlit as st
import pandas as pd

# read app vars in
app_vars = pd.read_csv("data/app_vars.csv")
seasons = app_vars["season"]

# page config
st.set_page_config(
    page_title="Points Projections • FPLalytics",
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
projections_df = pd.read_csv(
    "data/" + str(season_option)[:4] + "/points_projections.csv"
)
player_mapping = pd.read_csv("data/" + str(season_option)[:4] + "/player_mapping.csv")
team_mapping = pd.read_csv("data/" + str(season_option)[:4] + "/team_mapping.csv")
curr_gw = latest_gw + 1

# add fpl info
player_mapping = player_mapping.dropna(subset="fpl_id")
player_mapping["web_name_pos"] = (
    player_mapping["web_name"] + " " + player_mapping["pos"]
)
projections_df = projections_df.merge(
    player_mapping[
        ["player_id", "web_name_pos", "now_cost", "element_type", "team_id"]
    ],
    how="left",
    on="player_id",
)
# add team name
projections_df = projections_df.merge(
    team_mapping[["team_id", "team_short"]], how="left", on="team_id"
)
projections_df = projections_df.drop(columns="team_id")

# title and information
st.title("Points Projections")
if latest_gw == 38:
    st.caption(
        ":warning: Post-Season View",
        help="Post-season view displays the final 6 gameweeks.",
    )
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to compare projected points for players and inform your transfer decisions. 
        Data tables can be downloaded, searched, and expanded with tooltip that appears on mouse hover.

Points projections are calculated by an expected value model that takes weighted historical performance statistics as inputs. 

The model considers the following:
* player historical npxG performance
* player historical xA performance
* team historical xGC performance
* opponent team offensive and defensive strength
* home / away fixtures
* expected penalties
* goalkeeper historical saves performance
* player historical FPL bonus points
 """
    )

# options
with st.expander("Options", expanded=False):
    # gameweek lookahead slider
    if curr_gw < 38:
        gw_lookahead = st.slider(
            "Gameweek Lookahead", curr_gw, 38, min(curr_gw + 5, 38)
        )
    else:
        gw_lookahead = 38
    # price filter
    price_filter = st.slider(
        "Max Price",
        min_value=projections_df["now_cost"].min(),
        max_value=projections_df["now_cost"].max(),
        value=projections_df["now_cost"].max(),
        step=0.1,
        format="£%.1fm",
    )


# filter based on price selection
projections_df = projections_df[projections_df["now_cost"] <= price_filter]

# get column names for formatting
all_columns = projections_df.columns.to_list()
gameweek_columns = [
    x
    for x in all_columns
    if x
    not in [
        "player_id",
        "minutes",
        "web_name_pos",
        "now_cost",
        "element_type",
        "team_short",
    ]
]

# filter gameweeks
gameweek_columns = gameweek_columns[curr_gw - 1 : gw_lookahead]

# get total points over gameweek range
projections_df["Total"] = projections_df[gameweek_columns].sum(axis=1)

# sort values by next gameweek projected points
projections_df = projections_df.sort_values(by="Total", ascending=False)


# subset by position
forwards_df = projections_df[projections_df["element_type"] == 4]
midfielders_df = projections_df[projections_df["element_type"] == 3]
defenders_df = projections_df[projections_df["element_type"] == 2]
goalkeepers_df = projections_df[projections_df["element_type"] == 1]

# tab setup
by_pos_tab, combine_tab = st.tabs(["By Position", "Combined"])

with by_pos_tab:
    # forwards points projections visualization
    st.header("Forwards")
    st.dataframe(
        forwards_df.style.background_gradient(
            axis=0, subset=gameweek_columns, cmap="RdYlGn"
        )
        .background_gradient(axis=0, subset="now_cost", cmap="Blues")
        .background_gradient(axis=0, subset="Total", cmap="Blues")
        .background_gradient(axis=0, subset="minutes", cmap="Blues")
        .format({"now_cost": "£{:.1f}m", "minutes": "{:.0f}"}, precision=2),
        column_config={
            "web_name_pos": "Player",
            "team_short": "Team",
            "now_cost": st.column_config.NumberColumn("Price", help="FPL Price"),
            "minutes": "xMinutes",
            "Total": st.column_config.NumberColumn(
                help="Total predicted points over gameweek range."
            ),
        },
        column_order=(
            ["web_name_pos", "team_short", "now_cost", "minutes"]
            + gameweek_columns
            + ["Total"]
        ),
        hide_index=True,
        use_container_width=True,
    )

    # midfielders points projections visualization
    st.header("Midfielders")
    st.dataframe(
        midfielders_df.style.background_gradient(
            axis=0, subset=gameweek_columns, cmap="RdYlGn"
        )
        .background_gradient(axis=0, subset="now_cost", cmap="Blues")
        .background_gradient(axis=0, subset="Total", cmap="Blues")
        .background_gradient(axis=0, subset="minutes", cmap="Blues")
        .format({"now_cost": "£{:.1f}m", "minutes": "{:.0f}"}, precision=2),
        column_config={
            "web_name_pos": "Player",
            "team_short": "Team",
            "now_cost": st.column_config.NumberColumn("Price", help="FPL Price"),
            "minutes": "xMinutes",
            "Total": st.column_config.NumberColumn(
                help="Total predicted points over gameweek range."
            ),
        },
        column_order=(
            ["web_name_pos", "team_short", "now_cost", "minutes"]
            + gameweek_columns
            + ["Total"]
        ),
        hide_index=True,
        use_container_width=True,
    )

    # Defenders points projections visualization
    st.header("Defenders")
    st.dataframe(
        defenders_df.style.background_gradient(
            axis=0, subset=gameweek_columns, cmap="RdYlGn"
        )
        .background_gradient(axis=0, subset="now_cost", cmap="Blues")
        .background_gradient(axis=0, subset="Total", cmap="Blues")
        .background_gradient(axis=0, subset="minutes", cmap="Blues")
        .format({"now_cost": "£{:.1f}m", "minutes": "{:.0f}"}, precision=2),
        column_config={
            "web_name_pos": "Player",
            "team_short": "Team",
            "now_cost": st.column_config.NumberColumn("Price", help="FPL Price"),
            "minutes": "xMinutes",
            "Total": st.column_config.NumberColumn(
                help="Total predicted points over gameweek range."
            ),
        },
        column_order=(
            ["web_name_pos", "team_short", "now_cost", "minutes"]
            + gameweek_columns
            + ["Total"]
        ),
        hide_index=True,
        use_container_width=True,
    )

    # Goalkeepers points projections visualization
    st.header("Goalkeepers")
    st.dataframe(
        goalkeepers_df.style.background_gradient(
            axis=0, subset=gameweek_columns, cmap="RdYlGn"
        )
        .background_gradient(axis=0, subset="now_cost", cmap="Blues")
        .background_gradient(axis=0, subset="Total", cmap="Blues")
        .background_gradient(axis=0, subset="minutes", cmap="Blues")
        .format({"now_cost": "£{:.1f}m", "minutes": "{:.0f}"}, precision=2),
        column_config={
            "web_name_pos": "Player",
            "team_short": "Team",
            "now_cost": st.column_config.NumberColumn("Price", help="FPL Price"),
            "minutes": "xMinutes",
            "Total": st.column_config.NumberColumn(
                help="Total predicted points over gameweek range."
            ),
        },
        column_order=(
            ["web_name_pos", "team_short", "now_cost", "minutes"]
            + gameweek_columns
            + ["Total"]
        ),
        hide_index=True,
        use_container_width=True,
    )

with combine_tab:
    # all players points projections visualization
    st.header("All Players")
    st.dataframe(
        projections_df.style.background_gradient(
            axis=0, subset=gameweek_columns, cmap="RdYlGn"
        )
        .background_gradient(axis=0, subset="now_cost", cmap="Blues")
        .background_gradient(axis=0, subset="Total", cmap="Blues")
        .background_gradient(axis=0, subset="minutes", cmap="Blues")
        .format({"now_cost": "£{:.1f}m", "minutes": "{:.0f}"}, precision=2),
        column_config={
            "web_name_pos": "Player",
            "team_short": "Team",
            "now_cost": st.column_config.NumberColumn("Price", help="FPL Price"),
            "minutes": "xMinutes",
            "Total": st.column_config.NumberColumn(
                help="Total predicted points over gameweek range."
            ),
        },
        column_order=(
            ["web_name_pos", "team_short", "now_cost", "minutes"]
            + gameweek_columns
            + ["Total"]
        ),
        hide_index=True,
        use_container_width=True,
    )
