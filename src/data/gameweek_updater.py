import sys
from get_fixture_data import get_fixture_data_func
from get_player_data import get_player_data_func

# odm dir
sys.path.append("src/models")
from odm import odm_func

# read in finished gameweek from user input
GW = int(sys.argv[1])

# run data and model scripts
get_fixture_data_func(GW)
odm_func(GW + 1)
get_player_data_func()
