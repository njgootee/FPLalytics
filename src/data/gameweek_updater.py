import sys
import pandas as pd
from data.get_fixture_data import get_fixture_data
from data.get_player_data import get_player_data
from data.player_mapping_updater import get_fpl_player_maps
from models.odm import odm_func


# read in finished gameweek from user input
GW = int(sys.argv[1])
SEASON = sys.argv[2]

# run data and model scripts
get_fixture_data(GW, SEASON)
odm_func(GW + 1, SEASON)
get_player_data(SEASON)
get_fpl_player_maps(SEASON)

# update app vars
app_vars = pd.read_csv("data/app_vars.csv")
app_vars.loc[app_vars["season"].str[:4] == SEASON, "latest_gameweek"] = GW
app_vars.to_csv("data/app_vars.csv", index=False)
