from understatapi import UnderstatClient
import pandas as pd
import numpy as np
import sys


def get_season_data(season):
    """Retrieve fixture schedule from Understat at beginning of new season

    Args:
        season (str): start year of EPL season to retrieve
    """
    with UnderstatClient() as understat:
        # All matches in season
        fixtures = pd.DataFrame(understat.league(league="EPL").get_match_data(season))

    # extract team names
    fixtures["home"] = (
        fixtures["h"]
        .astype(str)
        .str.extract(r"\'title': '([a-zA-Z\s]*)'", expand=False)
    )
    fixtures["away"] = (
        fixtures["a"]
        .astype(str)
        .str.extract(r"\'title': '([a-zA-Z\s]*)'", expand=False)
    )

    # format
    fixtures = fixtures.drop(
        columns=[
            "isResult",
            "h",
            "a",
            "goals",
            "xG",
            "forecast",
        ]
    )
    fixtures.rename(columns={"id": "fixture_id"}, inplace=True)
    fixtures["datetime"] = pd.to_datetime(
        fixtures["datetime"], format="%Y-%m-%d %H:%M:%S"
    )

    # map home teams to ids
    team_mapping = pd.read_csv("data/" + season + "/team_mapping.csv")
    fixtures = fixtures.merge(
        team_mapping[["team_id", "team"]], how="left", left_on="home", right_on="team"
    )
    fixtures.drop(columns={"team"}, inplace=True)
    fixtures.rename(columns={"team_id": "h_id"}, inplace=True)

    # map away teams to ids
    fixtures = fixtures.merge(
        team_mapping[["team_id", "team"]], how="left", left_on="away", right_on="team"
    )
    fixtures.drop(columns={"team"}, inplace=True)
    fixtures.rename(columns={"team_id": "a_id"}, inplace=True)

    # add gameweek number
    fixtures["gameweek"] = np.repeat(np.arange(1, 39), 10)

    # save file
    fixtures.to_csv("data/" + season + "/season_data.csv", index=False)


if __name__ == "__main__":
    get_season_data(sys.argv[1])
