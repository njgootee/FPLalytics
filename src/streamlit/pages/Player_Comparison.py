import streamlit as st
import pandas as pd
import numpy as np
from functions.generate_fixture_df import generate_fixtures_df

# ----------------------------------------------------------------------#
# Session state storage, callback functions
# ----------------------------------------------------------------------#

# session state storage
if "row_selection" not in st.session_state:
    st.session_state.row_selection = []
if "player_selection" not in st.session_state:
    st.session_state.player_selection = []


# performance dataframe row select callback function
def row_selection_func():
    st.session_state.row_selection = st.session_state.df.selection.rows


# filter by select players button callback function
def filter_button_func(selected_players):
    st.session_state.player_selection = selected_players


def main():
    # ----------------------------------------------------------------------#
    # Page and data initial setup
    # ----------------------------------------------------------------------#
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
        latest_gw = app_vars[app_vars["season"] == season_option][
            "latest_gameweek"
        ].item()
        st.caption(
            """Latest gameweek data: :blue["""
            + str(latest_gw)
            + """]  
                    [GitHub](https://github.com/njgootee)"""
        )

    # read data in
    player_data = pd.read_csv("data/" + str(season_option)[:4] + "/player_data.csv")
    player_mapping = pd.read_csv(
        "data/" + str(season_option)[:4] + "/player_mapping.csv"
    )
    team_mapping = pd.read_csv("data/" + str(season_option)[:4] + "/team_mapping.csv")
    fixtures = pd.read_csv("data/" + str(season_option)[:4] + "/season_data.csv")
    odm_data = pd.read_csv("data/" + str(season_option)[:4] + "/odm_rating.csv")
    odm_data = odm_data.tail(20)
    curr_gw = latest_gw + 1

    # title and information
    st.title("Player Comparison")
    with st.expander("Information", expanded=False):
        st.markdown(
            """Use this tool to compare the performance statistics of players and inform your FPL transfer decisions.   
Utilize the filters in the options section to narrow your search for the perfect asset. Select players from the Performance Stats dataframe and expand the other sections for a holistic and detailed comparison."""
        )

    # add fpl info to player data
    player_mapping = player_mapping.dropna(subset="fpl_id")
    player_mapping["web_name_pos"] = (
        player_mapping["web_name"] + " " + player_mapping["pos"]
    )
    player_data = player_data.merge(
        player_mapping[
            ["player_id", "web_name_pos", "element_type", "now_cost", "penalties_order"]
        ],
        how="left",
        on="player_id",
    )
    player_data = player_data.dropna(subset="web_name_pos")
    player_data = player_data.merge(
        team_mapping[["team_id", "team_short"]], how="left", on="team_id"
    )
    # ----------------------------------------------------------------------#
    # Options
    # ----------------------------------------------------------------------#
    with st.expander("Options", expanded=False):
        st.write("#### Player Filters")
        # player postion option
        pos_filter = st.multiselect(
            "Player Positions",
            ["GKP", "DEF", "MID", "FWD"],
            ["GKP", "DEF", "MID", "FWD"],
        )
        # filter by player position
        pos_dict = {"GKP": 1, "DEF": 2, "MID": 3, "FWD": 4}
        pos_num_filter = [pos_dict[pos] for pos in pos_filter]
        player_data = player_data[player_data["element_type"].isin(pos_num_filter)]
        # options columns
        pf_col1, pf_col2 = st.columns(2, gap="large")
        # player price option
        with pf_col1:
            price_filter = st.slider(
                "Max Price",
                min_value=player_data["now_cost"].min(),
                max_value=player_data["now_cost"].max(),
                value=player_data["now_cost"].max(),
                step=0.1,
                format="£%.1fm",
            )
            # filter by player price
            player_data = player_data[player_data["now_cost"] <= price_filter]
        # minutes per appearance option
        with pf_col2:
            mpa_filter = st.slider(
                "Minimum Minutes Per Appearance",
                1,
                90,
                60,
            )
        # selected players option
        player_filter = st.multiselect(
            "Display Only Selected Players",
            player_data["player_id"].unique(),
            format_func=lambda x: player_data[player_data["player_id"] == x][
                "web_name_pos"
            ].values[-1]
            + " ["
            + player_data[player_data["player_id"] == x]["team_short"].values[-1]
            + "]",
            default=st.session_state.player_selection,
        )
        # filter by selected players
        if len(player_filter) > 0:
            player_data = player_data[player_data["player_id"].isin(player_filter)]

        st.divider()
        st.write("#### Fixture Filters")
        ff_col1, ff_col2 = st.columns(2, gap="large")
        # select gameweek range
        with ff_col1:
            gw_range = st.slider("Gameweek Range", 1, latest_gw, (1, latest_gw))
            # filter by gameweek range
            player_data = player_data[
                (player_data["gameweek"] >= gw_range[0])
                & (player_data["gameweek"] <= gw_range[1])
            ]
        # select gameweek lookahead
        with ff_col2:
            gw_lookahead = st.slider(
                "Gameweek Lookahead", latest_gw + 1, 38, min(latest_gw + 6, 38)
            )

        st.divider()
        st.write("#### Stat Filters")
        # stat aggregation
        agg_option = st.selectbox(
            "Performance Stats Aggregation", ("Per 90 Mins", "Totals")
        )

    # ----------------------------------------------------------------------#
    # Performance dataframe setup
    # ----------------------------------------------------------------------#
    # calculated stats
    player_data["npgoals"] = player_data["goals"] - player_data["penalty_scored"]
    player_data["npGI"] = player_data["npgoals"] + player_data["assists"]
    player_data["npshots"] = player_data["shots"] - player_data["penalty_attempt"]
    player_data["t_score"] = (player_data["npxGI"] / player_data["team_xG"]) * 100
    player_data["xG_perc"] = (player_data["npxG"] / player_data["npxGI"]) * 100
    # groupby
    perf_df = player_data.groupby(["player_id"], as_index=False).agg(
        web_name_pos=("web_name_pos", "last"),
        npGI=("npGI", "sum"),
        npxGI=("npxGI", "sum"),
        xG_perc=("xG_perc", "mean"),
        t_score=("t_score", "mean"),
        npgoals=("npgoals", "sum"),
        npxG=("npxG", "sum"),
        shots=("npshots", "sum"),
        assists=("assists", "sum"),
        xA=("xA", "sum"),
        key_passes=("key_passes", "sum"),
        team=("team_name", "last"),
        team_short=("team_short", "last"),
        now_cost=("now_cost", "last"),
        appearances=("web_name_pos", "count"),
        penalties_order=("penalties_order", "last"),
        penalties=("penalty_scored", "sum"),
        time=("time", "sum"),
        yc=("yellow_card", "sum"),
        rc=("red_card", "sum"),
        team_xG=("team_xG", "sum"),
    )
    # minutes per appearance
    perf_df["mpa"] = perf_df["time"] / perf_df["appearances"]
    # filter by minutes per appearance
    perf_df = perf_df[perf_df["mpa"] >= mpa_filter]
    # team ratings
    perf_df = perf_df.merge(
        odm_data[["team", "o_rating_season", "d_rating_season"]], on="team"
    )
    # per 90 min aggregation
    if agg_option == "Per 90 Mins":
        perf_df["npGI"] = perf_df["npGI"] / perf_df["time"] * 90
        perf_df["npxGI"] = perf_df["npxGI"] / perf_df["time"] * 90
        perf_df["npgoals"] = perf_df["npgoals"] / perf_df["time"] * 90
        perf_df["npxG"] = perf_df["npxG"] / perf_df["time"] * 90
        perf_df["shots"] = perf_df["shots"] / perf_df["time"] * 90
        perf_df["assists"] = perf_df["assists"] / perf_df["time"] * 90
        perf_df["xA"] = perf_df["xA"] / perf_df["time"] * 90
        perf_df["key_passes"] = perf_df["key_passes"] / perf_df["time"] * 90

    # default sort
    perf_df = perf_df.sort_values("npxGI", ascending=False)

    # ----------------------------------------------------------------------#
    # Upcoming and past fixtures dataframe setup
    # ----------------------------------------------------------------------#
    # past fixtures
    past_fixtures2, temp, temp, temp, temp, temp, temp, temp = generate_fixtures_df(
        fixtures, team_mapping, odm_data, gw_range[0], gw_range[1]
    )

    # upcoming fixtures
    o_fx, o_fx_v, min_o, max_o, d_fx, d_fx_v, min_d, max_d = generate_fixtures_df(
        fixtures, team_mapping, odm_data, curr_gw, gw_lookahead
    )

    # ----------------------------------------------------------------------#
    # Performance dataframe
    # ----------------------------------------------------------------------#
    st.markdown("### Performance Stats")
    st.dataframe(
        perf_df.style.background_gradient(
            axis=0,
            subset=[
                "npGI",
                "npxGI",
                "xG_perc",
                "t_score",
            ],
            cmap="Blues",
        )
        .background_gradient(
            axis=0,
            subset=["npgoals", "npxG", "shots"],
            cmap="Purples",
        )
        .background_gradient(
            axis=0,
            subset=["assists", "xA", "key_passes"],
            cmap="Greens",
        )
        .format(
            {"t_score": "{:.0f} %", "xG_perc": "{:.0f} %", "now_cost": "£{:.1f}m"},
            precision=2,
        ),
        column_config={
            "web_name_pos": "Player",
            "now_cost": st.column_config.NumberColumn("Price", help="FPL Price"),
            "npGI": st.column_config.NumberColumn(
                "npGI", help="Non-Penalty Goal Involvement: npGoals + Assists"
            ),
            "npxGI": st.column_config.NumberColumn(
                "npxGI", help="Non-Penalty Expected Goal Involvement: npxG + xA"
            ),
            "xG_perc": st.column_config.NumberColumn(
                "Goal Threat Bias",
                help="npxG as % of npxGI",
            ),
            "t_score": st.column_config.NumberColumn(
                "T-Score", help="Talisman Score: Player xGI as % of Team xG"
            ),
            "npgoals": st.column_config.NumberColumn(
                "npGoals", help="Non-Penalty Goals"
            ),
            "npxG": st.column_config.NumberColumn(
                "npxG", help="Non-Penalty Expected Goals"
            ),
            "shots": st.column_config.NumberColumn("npShots", help="Non-Penalty Shots"),
            "assists": "Assists",
            "xA": st.column_config.NumberColumn("xA", help="Expected Assists"),
            "key_passes": st.column_config.NumberColumn("KP", help="Key Passes"),
        },
        column_order=(
            [
                "web_name_pos",
                "now_cost",
                "npGI",
                "npxGI",
                "xG_perc",
                "t_score",
                "npgoals",
                "npxG",
                "shots",
                "assists",
                "xA",
                "key_passes",
            ]
        ),
        on_select=row_selection_func,
        selection_mode="multi-row",
        key="df",
        hide_index=True,
        use_container_width=True,
    )

    # user selected players from performance dataframe
    selected_players = perf_df.iloc[st.session_state.df.selection.rows][
        "player_id"
    ].to_list()
    selected_players_names = perf_df.iloc[st.session_state.df.selection.rows][
        "web_name_pos"
    ].to_list()

    # filter to selected players button
    st.button(
        label="Filter To Selected Players",
        on_click=filter_button_func,
        args=([selected_players]),
    )

    # filter performance dataframe for use in other data elements
    filtered_perf_df = perf_df[perf_df["web_name_pos"].isin(selected_players_names)]

    # ----------------------------------------------------------------------#
    # historical detail dataframe
    # ----------------------------------------------------------------------#
    with st.expander("Historical Detail"):
        if len(selected_players) > 0:
            # stat selection option
            stat_dict = {
                "time": "Minutes",
                "npGI": "npGI",
                "npxGI": "npxGI",
                "npgoals": "npGoals",
                "npxG": "npxG",
                "shots": "npShots",
                "assists": "Assists",
                "xA": "xA",
                "key_passes": "KP",
            }
            hist_stat_option = st.selectbox(
                "Select Stat",
                options=(
                    "time",
                    "npGI",
                    "npxGI",
                    "npgoals",
                    "npxG",
                    "shots",
                    "assists",
                    "xA",
                    "key_passes",
                ),
                index=2,
                format_func=lambda x: stat_dict.get(x),
                label_visibility="collapsed",
            )

            # opponent names
            past_fixtures = past_fixtures2.reset_index(names="team")
            past_fixtures = filtered_perf_df[["web_name_pos", "team"]].merge(
                past_fixtures, on="team", how="left"
            )
            past_fixtures = (
                past_fixtures.drop(columns=["team", "FR"])
                .rename(columns={"web_name_pos": "Player"})
                .set_index("Player")
                .reindex(selected_players_names)
            )

            # setup dataframe
            historical_df = (
                player_data[player_data["player_id"].isin(selected_players)]
                .pivot_table(
                    index="web_name_pos",
                    columns="gameweek",
                    values=hist_stat_option,
                    aggfunc="sum",
                )
                .reindex(selected_players_names)
            )
            historical_df = historical_df.round(2)
            historical_df = historical_df.add_prefix("GW ")
            historical_df2 = historical_df.astype("str") + " " + past_fixtures
            historical_df2 = historical_df2[historical_df.columns]

            # data element
            st.dataframe(
                historical_df2.style.background_gradient(
                    axis=None, cmap="Blues", gmap=historical_df
                ).format(precision=2),
                column_config={"web_name_pos": "Player"},
                use_container_width=True,
            )

        else:
            # help caption
            st.caption(
                "Select players in Performance Stats dataframe to view gameweek history of selected stat."
            )

    # ----------------------------------------------------------------------#
    # upcoming fixtures dataframe
    # ----------------------------------------------------------------------#
    with st.expander("Upcoming Fixtures"):
        # Dataframe
        if len(selected_players) > 0:
            o_tab, d_tab = st.tabs(["Offence", "Defence"])
            # offensive fixtures
            with o_tab:
                # adjust offensive fixtures dataframes from team basis to player basis
                o_fx = o_fx.reset_index(names="team")
                o_fx = filtered_perf_df[["web_name_pos", "team"]].merge(
                    o_fx, on="team", how="left"
                )
                o_fx = (
                    o_fx.drop(columns="team")
                    .rename(columns={"web_name_pos": "Player"})
                    .set_index("Player")
                    .reindex(selected_players_names)
                )

                o_fx_v = o_fx_v.reset_index(names="team")
                o_fx_v = filtered_perf_df[["web_name_pos", "team"]].merge(
                    o_fx_v, on="team", how="left"
                )
                o_fx_v = (
                    o_fx_v.drop(columns="team")
                    .rename(columns={"web_name_pos": "Player"})
                    .set_index("Player")
                    .reindex(selected_players_names)
                )
                # offensive dataframe
                st.dataframe(
                    o_fx.style.background_gradient(
                        axis=None,
                        cmap="RdYlGn",
                        gmap=o_fx_v,
                        vmax=max_d,
                        vmin=min_d,
                    )
                    .background_gradient(cmap="Blues", subset=["FR"])
                    .format({"FR": "{:1.0f} %"}),
                    column_config={
                        "FR": st.column_config.NumberColumn(
                            "FR", help="Fixture Ratio (% of mean fixture strength)"
                        ),
                    },
                    use_container_width=True,
                )

            # defensive fixtures
            with d_tab:
                # adjust defensive fixtures dataframes from team basis to player basis
                d_fx = d_fx.reset_index(names="team")
                d_fx = filtered_perf_df[["web_name_pos", "team"]].merge(
                    d_fx, on="team", how="left"
                )
                d_fx = (
                    d_fx.drop(columns="team")
                    .rename(columns={"web_name_pos": "Player"})
                    .set_index("Player")
                    .reindex(selected_players_names)
                )

                d_fx_v = d_fx_v.reset_index(names="team")
                d_fx_v = filtered_perf_df[["web_name_pos", "team"]].merge(
                    d_fx_v, on="team", how="left"
                )
                d_fx_v = (
                    d_fx_v.drop(columns="team")
                    .rename(columns={"web_name_pos": "Player"})
                    .set_index("Player")
                    .reindex(selected_players_names)
                )
                # defensive dataframe
                st.dataframe(
                    d_fx.style.background_gradient(
                        axis=None,
                        cmap="RdYlGn_r",
                        gmap=d_fx_v,
                        vmax=max_o,
                        vmin=min_o,
                    )
                    .background_gradient(cmap="Blues", subset=["FR"])
                    .format({"FR": "{:1.0f} %"}),
                    column_config={
                        "FR": st.column_config.NumberColumn(
                            "FR", help="Fixture Ratio (% of mean fixture strength)"
                        ),
                    },
                    use_container_width=True,
                )

        else:
            # help caption
            st.caption(
                "Select players in Performance Stats dataframe to view upcoming fixture information."
            )

    # ----------------------------------------------------------------------#
    # informational stats dataframe
    # ----------------------------------------------------------------------#
    with st.expander("Informational Stats"):
        if len(selected_players) > 0:
            st.dataframe(
                filtered_perf_df.style.background_gradient(
                    axis=0, subset=["o_rating_season"], cmap="Blues"
                )
                .background_gradient(axis=0, subset=["d_rating_season"], cmap="Blues_r")
                .highlight_between(subset="penalties_order", color="#60B4FF", right=1)
                .format(
                    {
                        "o_rating_season": "{:1.0f}",
                        "mpa": "{:1.0f}",
                        "now_cost": "£{:.1f}m",
                        "penalties_order": "{:.0f}",
                    },
                    precision=2,
                ),
                column_config={
                    "web_name_pos": "Player",
                    "now_cost": st.column_config.NumberColumn(
                        "Price", help="FPL Price"
                    ),
                    "team_short": "Team",
                    "minutes": "Minutes",
                    "appearances": "Appearances",
                    "mpa": st.column_config.NumberColumn(
                        "MPA", help="Minutes Per Appearance"
                    ),
                    "penalties_order": st.column_config.NumberColumn(
                        "Penalty Order", help="Penalty Taker Order"
                    ),
                    "penalties": st.column_config.NumberColumn(
                        "Penalties", help="Penalties Scored"
                    ),
                    "yc": st.column_config.NumberColumn("YC", help="Yellow Cards"),
                    "rc": st.column_config.NumberColumn("RC", help="Red Cards"),
                    "o_rating_season": st.column_config.NumberColumn(
                        "Team Offense", help="Team Offense Rating (season)"
                    ),
                    "d_rating_season": st.column_config.NumberColumn(
                        "Team Defense", help="Team Defense Rating (season)"
                    ),
                },
                column_order=(
                    "web_name_pos",
                    "now_cost",
                    "team_short",
                    "o_rating_season",
                    "d_rating_season",
                    "appearances",
                    "minutes",
                    "mpa",
                    "penalties_order",
                    "penalties",
                    "yc",
                    "rc",
                ),
                hide_index=True,
                use_container_width=True,
            )

        else:
            # help caption
            st.caption(
                "Select players in Performance Stats dataframe to view informational data and statistics."
            )


if __name__ == "__main__":
    main()
