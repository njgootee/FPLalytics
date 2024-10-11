import pandas as pd
import numpy as np


def generate_fixtures_df(
    fixtures,
    team_mapping,
    odm_rating,
    gw_start,
    gw_end,
    model_option = "Full Season",
    home_advantage=0.33,
):
    """Generate fixtures dataframes

    Args:
        fixtures (pandas dataframe): EPL season fixtures dataframe
        team_mapping (pandas dataframe): EPL team mapping dataframe
        odm_rating (pandas dataframe): ODM ratings of EPL teams
        gw_start (int): First gameweek to include
        gw_end (int): Last gameweek to include
        model_option (str): "Past 6 Gameweeks" or "Full Season" ODM ratings model
        home_advantage (float): Percentage by which home fixtures are stronger than away fixtures. Between [0-1], default=0.24.
    """

    # filter by gameweeks
    fixtures = fixtures[
        (fixtures["gameweek"] >= gw_start) & (fixtures["gameweek"] <= gw_end)
    ]

    # home fixtures
    home_fixtures = fixtures.rename(columns={"home": "team", "away": "opponent"})
    home_fixtures = home_fixtures.merge(
        team_mapping[["team_id", "team_short"]], left_on="a_id", right_on="team_id"
    )
    home_fixtures["team_short"] = "v" + home_fixtures["team_short"]

    # away fixtures
    away_fixtures = fixtures.rename(columns={"away": "team", "home": "opponent"})
    away_fixtures = away_fixtures.merge(
        team_mapping[["team_id", "team_short"]], left_on="h_id", right_on="team_id"
    )
    away_fixtures["team_short"] = "@" + away_fixtures["team_short"]

    # concat home and away fixtures
    fixtures = pd.concat([home_fixtures, away_fixtures])
    fixtures = fixtures.pivot_table(
        values="team_short", index="team", columns="gameweek", aggfunc=pd.unique
    )
    fixtures = fixtures.add_prefix("GW ")
    fixtures = fixtures.replace({np.nan: ""})

    # home and away scaling factors
    home_factor = 1.0 + home_advantage / 2
    away_factor = 1.0 - home_advantage / 2

    # use short team names in ODM ratings
    short_name_dict = dict(zip(team_mapping["team_name"], team_mapping["team_short"]))
    odm_rating = odm_rating.rename(columns={"team": "team_name"})
    odm_rating["team_name"] = odm_rating["team_name"].map(short_name_dict)

    # home odm ratings
    odm_home = odm_rating.copy()
    odm_home["team_name"] = "v" + odm_home["team_name"]

    # away odm ratings
    odm_away = odm_rating.copy()
    odm_away["team_name"] = "@" + odm_away["team_name"]

    # calculate odm ratings for input model and scaling factor
    if model_option == "Full Season":
        odm_home["o_rating_season"] = odm_home["o_rating_season"] / home_factor
        odm_home["d_rating_season"] = odm_home["d_rating_season"] * home_factor
        odm_away["o_rating_season"] = odm_away["o_rating_season"] / away_factor
        odm_away["d_rating_season"] = odm_away["d_rating_season"] * away_factor
        odm_rating = pd.concat([odm_home, odm_away], ignore_index=True)
        o_rating_dict = odm_rating.set_index("team_name")["o_rating_season"].to_dict()
        min_o_rating = min(o_rating_dict.values())
        max_o_rating = max(o_rating_dict.values())
        d_rating_dict = odm_rating.set_index("team_name")["d_rating_season"].to_dict()
        min_d_rating = min(d_rating_dict.values())
        max_d_rating = max(d_rating_dict.values())
    elif model_option == "Past 6 Gameweeks":
        odm_home["o_rating_psix"] = odm_home["o_rating_psix"] / home_factor
        odm_home["d_rating_psix"] = odm_home["d_rating_psix"] * home_factor
        odm_away["o_rating_psix"] = odm_away["o_rating_psix"] / away_factor
        odm_away["d_rating_psix"] = odm_away["d_rating_psix"] * away_factor
        odm_rating = pd.concat([odm_home, odm_away], ignore_index=True)
        o_rating_dict = odm_rating.set_index("team_name")["o_rating_psix"].to_dict()
        min_o_rating = min(o_rating_dict.values())
        max_o_rating = max(o_rating_dict.values())
        d_rating_dict = odm_rating.set_index("team_name")["d_rating_psix"].to_dict()
        min_d_rating = min(d_rating_dict.values())
        max_d_rating = max(d_rating_dict.values())

    # create offence data frames
    o_fixture_values = fixtures.map(
        lambda x: (
            (sum([d_rating_dict[i] for i in x])) / (len(x) - 1)
            if len(x) > 1
            else sum([d_rating_dict[i] for i in x])
        )
    )
    o_fixture_values = o_fixture_values.replace(0, min(d_rating_dict.values()) / 1.25)
    o_fixtures = fixtures.map(lambda x: ", ".join([i for i in x]))
    # calculate and add offensive fixture rating
    o_FR = pd.DataFrame(
        o_fixture_values.sum(axis=1) / o_fixture_values.sum(axis=1).mean() * 100,
        columns=["FR"],
    )
    o_fixtures = o_fixtures.merge(o_FR, left_index=True, right_index=True).sort_values(
        "FR", ascending=False
    )
    o_fixture_values = o_fixture_values.merge(
        o_FR, left_index=True, right_index=True
    ).sort_values("FR", ascending=False)

    # create defence data frames
    d_fixture_values = fixtures.map(
        lambda x: (
            (sum([o_rating_dict[i] for i in x])) / (len(x) + 1)
            if len(x) > 1
            else sum([o_rating_dict[i] for i in x])
        )
    )
    d_fixture_values = d_fixture_values.replace(0, max(o_rating_dict.values()) * 1.25)
    d_fixtures = fixtures.map(lambda x: ", ".join([i for i in x]))
    # calculate and add defensive fixture rating
    d_FR = pd.DataFrame(
        1 / (d_fixture_values.sum(axis=1) / d_fixture_values.sum(axis=1).mean()) * 100,
        columns=["FR"],
    )
    d_fixtures = d_fixtures.merge(d_FR, left_index=True, right_index=True).sort_values(
        "FR", ascending=False
    )
    d_fixture_values = d_fixture_values.merge(
        d_FR, left_index=True, right_index=True
    ).sort_values("FR", ascending=False)

    # return
    return (
        o_fixtures,
        o_fixture_values,
        min_o_rating,
        max_o_rating,
        d_fixtures,
        d_fixture_values,
        min_d_rating,
        max_d_rating,
    )
