import pandas as pd
import numpy as np
import requests
import sys


def get_fpl_player_data(gw, season):
    """Retrieve player performance data from FPL, via API request to Fantasy Premier League.

    Args:
        gw (int): FPL gameweek to assign to new data
        season (str): start year of EPL season to assign to new data
    """
    # read in existing data
    fpl_player_data = pd.read_csv("data/" + season + "/fpl_player_data.csv")

    # api request FPL for updated players
    r = requests.get("https://fantasy.premierleague.com/api/event/"+ str(gw) +"/live/").json()
    new_fpl_player_data = pd.json_normalize(r["elements"])

    #format
    new_fpl_player_data = new_fpl_player_data.rename(columns={
        'id': 'fpl_id',
        'stats.minutes': 'minutes',
        'stats.goals_scored': 'goals_scored',
        'stats.assists': 'assists',
        'stats.clean_sheets': 'clean_sheets',
        'stats.goals_conceded': 'goals_conceded',
        'stats.own_goals': 'own_goals',
        'stats.penalties_saved': 'penalties_saved',
        'stats.penalties_missed': 'penalties_missed',
        'stats.yellow_cards': 'yellow_cards',
        'stats.red_cards': 'red_cards',
        'stats.saves': 'saves',
        'stats.bonus': 'bonus',
        'stats.bps': 'bps',
        'stats.influence': 'influence',
        'stats.creativity': 'creativity',
        'stats.threat': 'threat',
        'stats.ict_index': 'ict_index',
        'stats.starts': 'starts',
        'stats.expected_goals': 'expected_goals',
        'stats.expected_assists': 'expected_assists',
        'stats.expected_goal_involvements': 'expected_goal_involvements',
        'stats.expected_goals_conceded': 'expected_goals_conceded',
        'stats.total_points': 'total_points',
        'stats.in_dreamteam': 'in_dreamteam'
    })
    new_fpl_player_data = new_fpl_player_data.drop(columns={'explain'})
    new_fpl_player_data['gameweek'] = gw

    # add new data to existing file
    fpl_player_data = pd.concat([fpl_player_data, new_fpl_player_data], ignore_index=True)

    # write updates
    fpl_player_data.to_csv("data/" + season + "/fpl_player_data.csv", index=False)


if __name__ == "__main__":
    get_fpl_player_data(int(sys.argv[1]), sys.argv[2])