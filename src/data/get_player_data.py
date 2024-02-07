from understatapi import UnderstatClient
import pandas as pd
import numpy as np


def get_player_data_func(GW):
    # read in existing data
    fixture_data = pd.read_csv("data/2023/fixture_data.csv")
    player_data = pd.read_csv("data/2023/player_data.csv")

    # get ids of resulted fixtures
    fixture_resulted_ids = fixture_data["fixture_id"].to_list()
    # get ids of fixtures already in database
    fixture_recorded_ids = player_data["fixture_id"].unique().tolist()
    # get ids of resulted fixtures not in database
    new_fixture_ids = list(
        map(str, list(set(fixture_resulted_ids) - set(fixture_recorded_ids)))
    )

    # iterate through matches not yet recorded
    for fixture_id in new_fixture_ids:
        # Get player performance data for fixture
        with UnderstatClient() as understat:
            roster_data = understat.match(match=str(fixture_id)).get_roster_data()
        home_players = pd.json_normalize([{**v} for k, v in roster_data["h"].items()])
        away_players = pd.json_normalize([{**v} for k, v in roster_data["a"].items()])
        new_player_data = pd.concat([home_players, away_players])

        # add fixture id feature
        new_player_data["fixture_id"] = int(fixture_id)
        # add gameweek feature
        new_player_data = new_player_data.merge(
            fixture_data[["fixture_id", "gameweek"]], on="fixture_id"
        )
        # consolidate team id
        new_player_data.rename(columns={"team_id": "team"}, inplace=True)
        new_player_data["team_id"] = new_player_data["team"].map(
            {
                "83": 0,
                "71": 1,
                "73": 2,
                "244": 3,
                "220": 4,
                "92": 5,
                "80": 6,
                "78": 7,
                "72": 8,
                "228": 9,
                "87": 10,
                "256": 11,
                "88": 12,
                "89": 13,
                "86": 14,
                "249": 15,
                "238": 16,
                "82": 17,
                "81": 18,
                "229": 19,
            }
        )
        # add team name
        new_player_data["team_name"] = new_player_data["team_id"].map(
            {
                0: "Arsenal",
                1: "Aston Villa",
                2: "Bournemouth",
                3: "Brentford",
                4: "Brighton",
                5: "Burnley",
                6: "Chelsea",
                7: "Crystal Palace",
                8: "Everton",
                9: "Fulham",
                10: "Liverpool",
                11: "Luton",
                12: "Manchester City",
                13: "Manchester United",
                14: "Newcastle United",
                15: "Nottingham Forest",
                16: "Sheffield United",
                17: "Tottenham",
                18: "West Ham",
                19: "Wolverhampton Wanderers",
            }
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
        # add xgi
        new_player_data["xGI"] = new_player_data["xG"] + new_player_data["xA"]
        # add new player data to database
        player_data = pd.concat([player_data, new_player_data], ignore_index=True)

    # sort
    player_data.sort_values(by=["gameweek", "team_id"], inplace=True)

    # write updates
    player_data.to_csv("data/2023/player_data.csv", index=False)
