from understatapi import UnderstatClient
import pandas as pd


def get_fixture_data_func(gw):
    """Retrieve fixture level data from Understat

    Args:
        gw (int): FPL gameweek to assign to new fixtures
    """
    with UnderstatClient() as understat:
        # All fixtures in season
        fixtures = pd.DataFrame(
            understat.league(league="EPL").get_match_data(season="2023")
        )
        # existing fixture database
        fixture_data = pd.read_csv("data/2023/fixture_data.csv")
        # get fixture ids of games that have already been played
        fixture_resulted_ids = pd.to_numeric(
            fixtures[fixtures["isResult"] == True]["id"]
        ).to_list()
        # get fixture ids of games already in database
        fixture_recorded_ids = fixture_data["fixture_id"].to_list()
        # get fixture ids of resulted games not in database
        new_fixture_ids = list(
            map(str, list(set(fixture_resulted_ids) - set(fixture_recorded_ids)))
        )
        # Add new fixture data to existing dataset
        for fixture in understat.match(new_fixture_ids):
            # get new fixture data, add gameweek, convenient team ids for algorithms
            new_fixture_data = pd.DataFrame(fixture.get_match_info(), index=[0])
            new_fixture_data["gameweek"] = gw
            new_fixture_data["h_id"] = new_fixture_data["team_h"].map(
                {
                    "Arsenal": 0,
                    "Aston Villa": 1,
                    "Bournemouth": 2,
                    "Brentford": 3,
                    "Brighton": 4,
                    "Burnley": 5,
                    "Chelsea": 6,
                    "Crystal Palace": 7,
                    "Everton": 8,
                    "Fulham": 9,
                    "Liverpool": 10,
                    "Luton": 11,
                    "Manchester City": 12,
                    "Manchester United": 13,
                    "Newcastle United": 14,
                    "Nottingham Forest": 15,
                    "Sheffield United": 16,
                    "Tottenham": 17,
                    "West Ham": 18,
                    "Wolverhampton Wanderers": 19,
                }
            )
            new_fixture_data["a_id"] = new_fixture_data["team_a"].map(
                {
                    "Arsenal": 0,
                    "Aston Villa": 1,
                    "Bournemouth": 2,
                    "Brentford": 3,
                    "Brighton": 4,
                    "Burnley": 5,
                    "Chelsea": 6,
                    "Crystal Palace": 7,
                    "Everton": 8,
                    "Fulham": 9,
                    "Liverpool": 10,
                    "Luton": 11,
                    "Manchester City": 12,
                    "Manchester United": 13,
                    "Newcastle United": 14,
                    "Nottingham Forest": 15,
                    "Sheffield United": 16,
                    "Tottenham": 17,
                    "West Ham": 18,
                    "Wolverhampton Wanderers": 19,
                }
            )
            # consolidate fixture id
            new_fixture_data.drop(columns=["fid"], inplace=True)
            new_fixture_data.rename(columns={"id": "fixture_id"}, inplace=True)
            # append fixture to current database
            fixture_data = pd.concat(
                [fixture_data, new_fixture_data], ignore_index=True
            )
    # write updates
    fixture_data.to_csv("data/2023/fixture_data.csv", index=False)
