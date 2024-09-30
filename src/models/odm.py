import pandas as pd
import numpy as np


def odm_func(gw, season):
    """Calculate offensive and defensive ratings of teams via the ODM model.
    Ratings for a given gameweek are the teams determined strengths before that gameweek has been played.

    Args:
        gw (int): FPL gameweek to assign to ratings
        season (str): start year of EPL season to retrieve
    """
    # read in team to id mapping
    team_mapping = pd.read_csv("data/" + season + "/team_mapping.csv")

    # read in fixture data
    fixture_data = pd.read_csv("data/" + season + "/fixture_data.csv")
    # setup season long and past 6 "form" model
    full_season = fixture_data[fixture_data["gameweek"] < gw]
    full_season.name = "full_season"
    past_six = fixture_data[
        (fixture_data["gameweek"] < gw) & (fixture_data["gameweek"] >= gw - 6)
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
            team_ids = team_mapping["team_id"].to_list()
            team_names = team_mapping["team_name"].to_list()
            rating_df = pd.DataFrame(
                data={
                    "team_id": team_ids,
                    "team": team_names,
                    "gameweek": gw,
                    "o_rating_season": o.flatten(),
                    "d_rating_season": d.flatten(),
                }
            )
        elif model.name == "past_six":
            rating_df["o_rating_psix"] = o.flatten()
            rating_df["d_rating_psix"] = d.flatten()

    # Append to existing rating database, write updates
    past_rating = pd.read_csv("data/" + season + "/odm_rating.csv")
    rating_df = pd.concat([past_rating, rating_df])
    rating_df.to_csv("data/" + season + "/odm_rating.csv", index=False)
