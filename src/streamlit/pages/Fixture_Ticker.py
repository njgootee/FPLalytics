import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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
    st.markdown(
        """Latest gameweek data: :blue["""
        + str(latest_gw)
        + """]  
                [GitHub](https://github.com/njgootee)"""
    )

# read data in
fixtures = pd.read_csv("data/" + str(season_option)[:4] + "/season_data.csv")
odm_data = pd.read_csv("data/" + str(season_option)[:4] + "/odm_rating.csv")
odm_data = odm_data.tail(20)
# curr_gw = latest_gw + 1
curr_gw = 33

# title and information
st.title("Fixture Ticker")
st.caption(
    ":warning: Post-Season View",
    help="Post-season view displays the final 6 gameweeks.",
)
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to compare upcoming fixture difficulty for different teams and asset types.

Enumerated columns represent upcoming gameweeks, while fixtures are shaded based on the opposition strength.
Opposition strength is determined by ODM Ratings: opponent defensive rating for the offence ticker, and opponent offensive rating for the defence ticker.
The Fixture Ratio (FR) represents the fixture strength, and is presented as a percentage of the mean fixture strength over the given gameweeks.

Change the gameweek scope and ODM data source in the options menu. The "Past 6 Gameweeks" option can be a better indicator of current fixture difficulty, but is more sensitive to outliers and variance."""
    )

# options
with st.expander("Options", expanded=False):
    # Model select box
    model_option = st.selectbox("Data Source", ("Full Season", "Past 6 Gameweeks"))

    # slider to filter upcoming gameweeks shown
    gw_option = st.slider(
        "Gameweek Range", curr_gw, 38, (curr_gw, min(curr_gw + 5, 38))
    )

# tab setup
o_tab, d_tab = st.tabs(["Offence", "Defence"])

# filter and transform
fixtures = fixtures[
    (fixtures["gameweek"] >= gw_option[0]) & (fixtures["gameweek"] <= gw_option[1])
]
home_fixtures = fixtures.rename(columns={"home": "team", "away": "opponent"})
away_fixtures = fixtures.rename(columns={"away": "team", "home": "opponent"})
fixtures = pd.concat([home_fixtures, away_fixtures])
fixtures = fixtures.pivot_table(
    values="opponent", index="team", columns="gameweek", aggfunc=pd.unique
)
fixtures.index.name = None
fixtures.columns.name = None
fixtures = fixtures.replace({np.nan: ""})

# get ratings
if model_option == "Full Season":
    o_rating_dict = odm_data.set_index("team")["o_rating_season"].to_dict()
    d_rating_dict = odm_data.set_index("team")["d_rating_season"].to_dict()
elif model_option == "Past 6 Gameweeks":
    o_rating_dict = odm_data.set_index("team")["o_rating_psix"].to_dict()
    d_rating_dict = odm_data.set_index("team")["d_rating_psix"].to_dict()

# short team names
short_name_dict = {
    "Arsenal": "ARS",
    "Aston Villa": "AVL",
    "Bournemouth": "BOU",
    "Brentford": "BRE",
    "Brighton": "BRI",
    "Burnley": "BUR",
    "Chelsea": "CHE",
    "Crystal Palace": "CRY",
    "Everton": "EVE",
    "Fulham": "FUL",
    "Liverpool": "LIV",
    "Luton": "LUT",
    "Manchester City": "MCI",
    "Manchester United": "MUN",
    "Newcastle United": "NEW",
    "Nottingham Forest": "NFO",
    "Sheffield United": "SHU",
    "Tottenham": "TOT",
    "West Ham": "WHU",
    "Wolverhampton Wanderers": "WOL",
}

# create offence data frames
o_fixture_values = fixtures.applymap(
    lambda x: (
        (sum([d_rating_dict[i] for i in x])) / (len(x) - 1)
        if len(x) > 1
        else sum([d_rating_dict[i] for i in x])
    )
)
o_fixture_values = o_fixture_values.replace(0, min(d_rating_dict.values()) / 1.25)
o_FR = pd.DataFrame(
    o_fixture_values.sum(axis=1) / o_fixture_values.sum(axis=1).mean() * 100,
    columns=["FR"],
)
o_fixtures = fixtures.applymap(lambda x: ", ".join([short_name_dict[i] for i in x]))
o_fixtures = o_fixtures.merge(o_FR, left_index=True, right_index=True).sort_values(
    "FR", ascending=False
)
o_fixture_values = o_fixture_values.merge(
    o_FR, left_index=True, right_index=True
).sort_values("FR", ascending=False)

# create defence data frames
d_fixture_values = fixtures.applymap(
    lambda x: (
        (sum([o_rating_dict[i] for i in x])) / (len(x) + 1)
        if len(x) > 1
        else sum([o_rating_dict[i] for i in x])
    )
)
d_fixture_values = d_fixture_values.replace(0, max(o_rating_dict.values()) * 1.25)
d_FR = pd.DataFrame(
    1 / (d_fixture_values.sum(axis=1) / d_fixture_values.sum(axis=1).mean()) * 100,
    columns=["FR"],
)
d_fixtures = fixtures.applymap(lambda x: ", ".join([short_name_dict[i] for i in x]))
d_fixtures = d_fixtures.merge(d_FR, left_index=True, right_index=True).sort_values(
    "FR", ascending=False
)
d_fixture_values = d_fixture_values.merge(
    d_FR, left_index=True, right_index=True
).sort_values("FR", ascending=False)

# offence fixtures
with o_tab:
    st.caption("Fixture difficulty for your offensive assets")
    st.dataframe(
        o_fixtures.style.background_gradient(
            axis=None,
            cmap="RdYlGn",
            gmap=o_fixture_values,
            subset=np.arange(gw_option[0], gw_option[1] + 1),
            vmax=max(d_rating_dict.values()),
            vmin=min(d_rating_dict.values()),
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
        d_fixtures.style.background_gradient(
            axis=None,
            cmap="RdYlGn_r",
            gmap=d_fixture_values,
            subset=np.arange(gw_option[0], gw_option[1] + 1),
            vmax=max(o_rating_dict.values()),
            vmin=min(o_rating_dict.values()),
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
