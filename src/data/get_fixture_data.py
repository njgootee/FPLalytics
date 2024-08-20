from understatapi import UnderstatClient
import pandas as pd
import sys


def get_fixture_data(gw, season):
    """Retrieve fixture level data from Understat

    Args:
        gw (int): FPL gameweek to assign to new fixtures
        season (str): start year of EPL season to retrieve
    """
    # read in team to id mapping
    team_mapping = pd.read_csv("data/" + season + "/team_mapping.csv")

    with UnderstatClient() as understat:
        # retrieve all fixtures in season
        fixtures = pd.DataFrame(
            understat.league(league="EPL").get_match_data(season=season)
        )
        # fixture ids of resulted games
        fixture_resulted_ids = pd.to_numeric(
            fixtures[fixtures["isResult"] == True]["id"]
        ).to_list()
        # existing fixture database
        fixture_data = pd.read_csv("data/" + season + "/fixture_data.csv")
        # get fixture ids of games already in database
        fixture_recorded_ids = fixture_data["fixture_id"].to_list()
        # get fixture ids of resulted games not in database
        new_fixture_ids = list(
            map(str, list(set(fixture_resulted_ids) - set(fixture_recorded_ids)))
        )

        # Add new fixture data to existing dataset
        for new_fixture in understat.match(new_fixture_ids):
            # get new fixture data
            new_fixture_data = pd.DataFrame(new_fixture.get_match_info(), index=[0])

            # add gameweek
            new_fixture_data["gameweek"] = gw

            # add home team id
            new_fixture_data = new_fixture_data.merge(
                team_mapping[["team_id", "team"]],
                how="left",
                left_on="team_h",
                right_on="team",
            )
            new_fixture_data.drop(columns={"team"}, inplace=True)
            new_fixture_data.rename(columns={"team_id": "h_id"}, inplace=True)

            # add away team id
            new_fixture_data = new_fixture_data.merge(
                team_mapping[["team_id", "team"]],
                how="left",
                left_on="team_a",
                right_on="team",
            )
            new_fixture_data.drop(columns={"team"}, inplace=True)
            new_fixture_data.rename(columns={"team_id": "a_id"}, inplace=True)

            # consolidate fixture id
            new_fixture_data.drop(columns=["fid"], inplace=True)
            new_fixture_data.rename(columns={"id": "fixture_id"}, inplace=True)

            # append fixture to current database
            fixture_data = pd.concat(
                [fixture_data, new_fixture_data], ignore_index=True
            )

    # write updates
    fixture_data.to_csv("data/" + season + "/fixture_data.csv", index=False)


if __name__ == "__main__":
    get_fixture_data(int(sys.argv[1]), sys.argv[2])
