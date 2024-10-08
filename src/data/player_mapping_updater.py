import pandas as pd
import numpy as np
import requests
import sys


def get_fpl_player_maps(season):
    """Retrieve player informational data from fantasy premier league and update player mapping file, via API request to Fantasy Premier League.

    Args:
        season (str): start year of EPL season
    """
    # read in existing data
    player_mapping = pd.read_csv("data/" + season + "/player_mapping.csv")

    # api request FPL for updated players
    r = requests.get("https://fantasy.premierleague.com/api/bootstrap-static/").json()
    fpl_player_data = pd.json_normalize(r["elements"])

    # filter out unavailable
    fpl_player_data = fpl_player_data[fpl_player_data["status"] != "u"]

    # format
    fpl_player_data["fpl_name"] = (
        fpl_player_data["first_name"] + " " + fpl_player_data["second_name"]
    )
    fpl_player_data["now_cost"] = fpl_player_data["now_cost"] / 10
    fpl_player_data["pos"] = np.select(
        condlist=[
            fpl_player_data["element_type"] == 1,
            fpl_player_data["element_type"] == 2,
            fpl_player_data["element_type"] == 3,
            fpl_player_data["element_type"] == 4,
        ],
        choicelist=["(G)", "(D)", "(M)", "(F)"],
    )
    fpl_player_data["team_id"] = fpl_player_data["team"] - 1
    fpl_player_data = fpl_player_data.rename(columns={"id": "fpl_id"})
    fpl_player_data = fpl_player_data[
        [
            "fpl_id",
            "fpl_name",
            "web_name",
            "element_type",
            "now_cost",
            "pos",
            "status",
            "team_id",
            "total_points",
        ]
    ]

    # merge with existing mapping
    fpl_player_data = fpl_player_data.merge(
        player_mapping[["player_id", "player", "fpl_id", "penalties_order"]],
        how="left",
        on="fpl_id",
    )
    fpl_player_data = fpl_player_data[
        [
            "player_id",
            "player",
            "fpl_id",
            "fpl_name",
            "web_name",
            "element_type",
            "pos",
            "now_cost",
            "penalties_order",
            "status",
            "team_id",
            "total_points",
        ]
    ]

    # players without mapping warning
    no_mapping = fpl_player_data[
        (fpl_player_data["player_id"].isna()) & (fpl_player_data["total_points"] > 0)
    ]["web_name"].to_list()
    if len(no_mapping) > 0:
        print("WARNING no mapping exists for: ")
        for player in no_mapping:
            print(player)

    # remove total points
    fpl_player_data = fpl_player_data.drop(columns="total_points")

    # write updates
    fpl_player_data.to_csv("data/" + season + "/player_mapping.csv", index=False)


if __name__ == "__main__":
    get_fpl_player_maps(sys.argv[1])
