from understatapi import UnderstatClient
import pandas as pd
import numpy as np
import sys


def odm_func(GW):
    # read in fixture data, setup dataframes for season long model and past 6 "form" model
    fixture_data = pd.read_csv("data/2023/fixture_data.csv")
    full_season = fixture_data[fixture_data["gameweek"] < GW]
    full_season.name = "full_season"
    past_six = fixture_data[
        (fixture_data["gameweek"] < GW) & (fixture_data["gameweek"] >= GW - 6)
    ]
    past_six.name = "past_six"
    models = [full_season, past_six]

    for model in models:
        # Create 'A' score matrix with small perturbation to aid convergence
        A = np.zeros((20, 20)) + 0.0001
        # Score team j got vs team i: A[i,j] = j team xG
        temp_arr = np.zeros((20, 20))
        temp_arr[model["h_id"], model["a_id"]] += model["a_xg"] * 100
        temp_arr[model["a_id"], model["h_id"]] += model["h_xg"] * 100
        A += temp_arr

        # ODM MODEL: iteratively update offensive and defensive ratings
        d = np.ones((20, 1))
        for k in range(10000):
            o = np.dot(A.T, (1 / d))
            d = np.dot(A, (1 / o))

        # Construct Rating Dataframe
        if model.name == "full_season":
            team_ids = [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
            ]
            team_list = [
                "Arsenal",
                "Aston Villa",
                "Bournemouth",
                "Brentford",
                "Brighton",
                "Burnley",
                "Chelsea",
                "Crystal Palace",
                "Everton",
                "Fulham",
                "Liverpool",
                "Luton",
                "Manchester City",
                "Manchester United",
                "Newcastle United",
                "Nottingham Forest",
                "Sheffield United",
                "Tottenham",
                "West Ham",
                "Wolverhampton Wanderers",
            ]
            rating_df = pd.DataFrame(
                data={
                    "team_id": team_ids,
                    "team": team_list,
                    "gameweek": GW,
                    "o_rating_season": o.flatten(),
                    "d_rating_season": d.flatten(),
                }
            )
        elif model.name == "past_six":
            rating_df["o_rating_psix"] = o.flatten()
            rating_df["d_rating_psix"] = d.flatten()

    # Append to existing rating database, write updates
    past_rating = pd.read_csv("data/2023/odm_rating.csv")
    rating_df = pd.concat([past_rating, rating_df])
    rating_df.to_csv("data/2023/odm_rating.csv", index=False)
