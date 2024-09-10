from understatapi import UnderstatClient
import pandas as pd
import numpy as np
import sys


def get_player_data(season):
    """Retrieve player level (per fixture) data from Understat. Use after get_fixture_data.py completed.

    Args:
        season (str): start year of EPL season to retrieve
    """
    # read in existing data
    fixture_data = pd.read_csv("data/" + season + "/fixture_data.csv")
    player_data = pd.read_csv("data/" + season + "/player_data.csv")
    team_mapping = pd.read_csv("data/" + season + "/team_mapping.csv")

    # get ids of resulted fixtures
    fixture_resulted_ids = fixture_data["fixture_id"].to_list()
    # get ids of fixtures already in database
    fixture_recorded_ids = player_data["fixture_id"].unique().tolist()
    # get ids of resulted fixtures not in database
    new_fixture_ids = list(
        map(str, list(set(fixture_resulted_ids) - set(fixture_recorded_ids)))
    )

    # iterate through matches not yet recorded
    for new_fixture in new_fixture_ids:
        with UnderstatClient() as understat:
            curr_match = understat.match(match=str(new_fixture))
            # Get player performance data
            roster_data = curr_match.get_roster_data()
            # Get shot data
            shot_data = curr_match.get_shot_data()

        # setup player data dataframe
        home_players = pd.json_normalize([{**v} for k, v in roster_data["h"].items()])
        away_players = pd.json_normalize([{**v} for k, v in roster_data["a"].items()])
        new_player_data = pd.concat([home_players, away_players])

        # setup penalties dataframe
        home_shots = pd.DataFrame(shot_data["h"])
        away_shots = pd.DataFrame(shot_data["a"])
        shots = pd.concat([home_shots, away_shots])
        penalties = shots[shots["situation"] == "Penalty"].reset_index()
        penalty_xG = float(penalties["xG"].max())
        if penalties.empty:
            penalty_xG = 0.0
        penalties["penalty_attempt"] = 1
        penalties["penalty_scored"] = np.where(penalties["result"] == "Goal", 1, 0)
        penalties = penalties[
            ["player_id", "match_id", "penalty_attempt", "penalty_scored"]
        ].rename(columns={"match_id": "fixture_id"})
        penalties = penalties.astype("int64")
        penalties = penalties.groupby(
            by=["player_id", "fixture_id"], as_index=False
        ).sum()

        # add fixture id feature
        new_player_data["fixture_id"] = int(new_fixture)

        # add gameweek feature
        new_player_data = new_player_data.merge(
            fixture_data[["fixture_id", "gameweek"]], on="fixture_id"
        )

        # consolidate team id
        new_player_data.rename(columns={"team_id": "understat_team_id"}, inplace=True)
        new_player_data["understat_team_id"] = new_player_data[
            "understat_team_id"
        ].astype("int")
        new_player_data = new_player_data.merge(
            team_mapping[["understat_team_id", "team_id", "team_name"]],
            how="left",
            on="understat_team_id",
        )

        # add team xg data
        new_player_data = new_player_data.merge(
            fixture_data[["fixture_id", "h_xg", "a_xg"]], on="fixture_id"
        )
        new_player_data["team_xG"] = np.where(
            new_player_data["h_a"] == "h",
            new_player_data["h_xg"],
            new_player_data["a_xg"],
        )

        # adjust dtypes
        new_player_data["xG"] = new_player_data["xG"].astype(float)
        new_player_data["xA"] = new_player_data["xA"].astype(float)
        new_player_data["fixture_id"] = new_player_data["fixture_id"].astype("int64")
        new_player_data["player_id"] = new_player_data["player_id"].astype("int64")

        # add xgi
        new_player_data["xGI"] = new_player_data["xG"] + new_player_data["xA"]

        # add pen data, calculate non pen xg and xgi
        new_player_data = new_player_data.merge(
            penalties, how="left", on=["fixture_id", "player_id"]
        )
        new_player_data["penalty_attempt"] = (
            new_player_data["penalty_attempt"].fillna(0).astype("int64")
        )
        new_player_data["penalty_scored"] = (
            new_player_data["penalty_scored"].fillna(0).astype("int64")
        )
        new_player_data["npxG"] = (
            new_player_data["xG"] - new_player_data["penalty_attempt"] * penalty_xG
        )
        new_player_data["npxGI"] = new_player_data["npxG"] + new_player_data["xA"]

        # add new player data to database
        player_data = pd.concat([player_data, new_player_data], ignore_index=True)

    # sort
    player_data.sort_values(by=["gameweek", "team_id"], inplace=True)

    # write updates
    player_data.to_csv("data/" + season + "/player_data.csv", index=False)


if __name__ == "__main__":
    get_player_data(sys.argv[1])
