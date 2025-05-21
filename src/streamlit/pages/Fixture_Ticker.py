import streamlit as st
import pandas as pd
from functions.generate_fixture_df import generate_fixtures_df

# read app vars in
app_vars = pd.read_csv("data/app_vars.csv")
seasons = app_vars["season"]

# page config
st.set_page_config(
    page_title="Fixture Ticker • FPLalytics",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

# sidebar
with st.sidebar:
    st.markdown(""":chart_with_upwards_trend: :blue[FPL]*alytics*""")
    season_option = st.selectbox("Season", seasons)
    latest_gw = app_vars[app_vars["season"] == season_option]["latest_gameweek"].item()
    st.caption(
        """Latest gameweek data: :blue["""
        + str(latest_gw)
        + """]  
                [GitHub](https://github.com/njgootee)"""
    )

# read data in
fixtures = pd.read_csv("data/" + str(season_option)[:4] + "/season_data.csv")
odm_data = pd.read_csv("data/" + str(season_option)[:4] + "/odm_rating.csv")
odm_data = odm_data.tail(20)
team_mapping = pd.read_csv("data/" + str(season_option)[:4] + "/team_mapping.csv")
curr_gw = latest_gw + 1
if latest_gw == 38:
    curr_gw = 33

# title and information
st.title("Fixture Ticker")
if latest_gw == 38:
    st.caption(
        ":warning: Post-Season View",
        help="Post-season view displays the final 6 gameweeks",
    )
if latest_gw < 6:
    st.caption(
        ":warning: Early Season View",
        help="ODM ratings are based on past season until Gameweek 7",
    )
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to compare upcoming fixture difficulty for different teams and asset types.

Home fixtures have a "v" prefix, away fixtures have an "@" prefix.
        
Fixtures are shaded based on the opposition strength, determined by the Team Ratings model: 
- opponent defensive rating for the offence ticker
- opponent offensive rating for the defence ticker
The Fixture Ratio (FR) represents the fixture strength, and is presented as a percentage of the mean fixture strength over the given gameweeks.

Change the gameweek scope, home advantage percentage, and ODM data source in the options menu. The "Past 6 Gameweeks" option can be a better indicator of current fixture difficulty, but is more sensitive to outliers and variance."""
    )

# options
with st.expander("Options", expanded=False):
    # Model select box
    model_option = st.selectbox("Data Source", ("Full Season", "Past 6 Gameweeks"))

    # slider to filter upcoming gameweeks shown
    if curr_gw < 38:
        gw_option = st.slider(
            "Gameweek Range", curr_gw, 38, (curr_gw, min(curr_gw + 5, 38))
        )
    else:
        gw_option = [38, 38]

    # slider to filter upcoming gameweeks shown
    home_advantage = st.slider("Home Advantage (%)", 0, 50, 33)
    home_advantage = home_advantage / 100

# generate fixtures dataframes
o_fx, o_fx_v, min_o, max_o, d_fx, d_fx_v, min_d, max_d = generate_fixtures_df(
    fixtures,
    team_mapping,
    odm_data,
    gw_option[0],
    gw_option[1],
    model_option,
    home_advantage,
)

# tab setup
o_tab, d_tab = st.tabs(["Offence", "Defence"])

# offence fixtures
with o_tab:
    st.caption("Fixture difficulty for your offensive assets")
    st.dataframe(
        o_fx.style.background_gradient(
            axis=None,
            cmap="RdYlGn",
            gmap=o_fx_v,
            vmax=max_d,
            vmin=min_d,
        )
        .background_gradient(cmap="Blues", subset=["FR"])
        .format({"FR": "{:1.0f} %"}),
        column_config={
            "FR": st.column_config.NumberColumn("FR", help="Fixture Ratio (% of mean)"),
        },
        use_container_width=True,
        height=737,
    )

# defence fixtures
with d_tab:
    st.caption("Fixture difficulty for your defensive assets")
    st.dataframe(
        d_fx.style.background_gradient(
            axis=None,
            cmap="RdYlGn_r",
            gmap=d_fx_v,
            vmax=max_o,
            vmin=min_o,
        )
        .background_gradient(cmap="Blues", subset=["FR"])
        .format({"FR": "{:1.0f} %"}),
        column_config={
            "FR": st.column_config.NumberColumn(
                "FR", help="Fixture Ratio (% of mean fixture strength)"
            ),
        },
        use_container_width=True,
        height=737,
    )
