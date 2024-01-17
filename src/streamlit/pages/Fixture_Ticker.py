import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# read data in
fixtures = pd.read_csv("data/2023/season_data.csv")
odm_data = pd.read_csv("data/2023/odm_rating.csv")
odm_data = odm_data.tail(20)
curr_gw = odm_data["gameweek"].max()

# page config
st.set_page_config(
    page_title="Fixture Ticker • FPLalytics", page_icon=":chart_with_upwards_trend:"
)

# sidebar
with st.sidebar:
    st.markdown(
        """:chart_with_upwards_trend: :blue[FPL]*alytics*  
                Latest gameweek data: :blue["""
        + str(curr_gw - 1)
        + """]  
                [GitHub](https://github.com/njgootee)"""
    )

# title and information
st.title("Fixture Ticker")
with st.expander("Information", expanded=False):
    st.markdown(
        """Use this tool to compare upcoming fixture difficulty for different teams and asset type.

Fixtures are shaded based on the opponents ODM ratings: opponent defensive rating for the offence ticker, and opponent offensive rating for the defence ticker.
Change the ODM rating data source in the options menu. The "Past 6 Gameweeks" option can be a better indicator of current fixture difficulty, but is more sensitive to outliers and variance.

The fixture ratio (FR) represents the fixture strength over the selected number of gameweeks."""
    )

# options
with st.expander("Options", expanded=False):
    # Model select box
    model_option = st.selectbox("Data Source", ("Full Season", "Past 6 Gameweeks"))

    # slider to select top/bottom n results
    n_gameweeks = st.slider("Number of Gameweeks", 2, 10, 6)

# tab setup
o_tab, d_tab = st.tabs(["Offence", "Defence"])

# filter and transform
fixtures = fixtures[
    (fixtures["gameweek"] >= curr_gw) & (fixtures["gameweek"] < curr_gw + n_gameweeks)
]
fixtures = fixtures.pivot_table(
    values="opponent", index="team", columns="gameweek", aggfunc="first"
)
fixtures.index.name = None
fixtures.columns.name = None

# get ratings
if model_option == "Full Season":
    o_rating_dict = odm_data.set_index("team")["o_rating_season"].to_dict()
    d_rating_dict = odm_data.set_index("team")["d_rating_season"].to_dict()
elif model_option == "Past 6 Gameweeks":
    o_rating_dict = odm_data.set_index("team")["o_rating_psix"].to_dict()
    d_rating_dict = odm_data.set_index("team")["d_rating_psix"].to_dict()

# create offence data frames
d_fixture_values = fixtures.replace(o_rating_dict).round(0).astype(int)
d_FR = pd.DataFrame(
    1 / (d_fixture_values.sum(axis=1) / d_fixture_values.sum(axis=1).mean()) * 100,
    columns=["FR"],
)
d_fixtures = fixtures.merge(d_FR, left_index=True, right_index=True).sort_values(
    "FR", ascending=False
)
d_fixture_values = d_fixture_values.merge(
    d_FR, left_index=True, right_index=True
).sort_values("FR", ascending=False)

# create defence data frames
o_fixture_values = fixtures.replace(d_rating_dict).round(2)
o_FR = pd.DataFrame(
    o_fixture_values.sum(axis=1) / o_fixture_values.sum(axis=1).mean() * 100,
    columns=["FR"],
)
o_fixtures = fixtures.merge(o_FR, left_index=True, right_index=True).sort_values(
    "FR", ascending=False
)
o_fixture_values = o_fixture_values.merge(
    o_FR, left_index=True, right_index=True
).sort_values("FR", ascending=False)

# short team names
o_fixtures = o_fixtures.replace(
    {
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
)

d_fixtures = d_fixtures.replace(
    {
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
)

# offence fixtures
with o_tab:
    st.caption("Fixture difficulty for your offensive assets")
    st.dataframe(
        o_fixtures.style.background_gradient(
            axis=None,
            cmap="RdYlGn",
            gmap=o_fixture_values,
            subset=np.arange(curr_gw, curr_gw + n_gameweeks),
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
            subset=np.arange(curr_gw, curr_gw + n_gameweeks),
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
