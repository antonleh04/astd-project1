"""
CO2 Emissions Analysis Dashboard
=================================
A Streamlit-based interactive dashboard for exploring global fossil-fuel CO2
emissions across countries, economic indicators, and industry sectors.

Data sources:
  - CO2 totals / per-capita / by sector (EDGARv8.0 via JRC)
  - GDP growth (World Bank API)
  - Land area (World Bank API)
  - Notable climate & economic events (curated CSV)

Layout:
  Tab 1 – The Big Picture    → aggregate trends, KPIs, treemap
  Tab 2 – Equity & Economy   → trajectory, cross-correlation
  Tab 3 – Sectoral Deep Dive → stacked area, sector treemap
"""

import streamlit as st
import pandas as pd

from config import COUNTRY_PRESETS, CUSTOM_CSS
from data_loader import (
    load_co2_data,
    load_events_data,
    load_land_area_data,
    load_gdp_data,
)
from visualizations import render_tab1_charts, render_tab2_charts, render_tab3_charts


# =============================================================================
# 1. PAGE CONFIG & CSS THEMING
# =============================================================================

st.set_page_config(
    page_title="ALLSTAT CO2 Dashboard",
    layout="wide",
    page_icon="\U0001F30D",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# 2. LOAD ALL DATASETS
# =============================================================================

try:
    df_totals, df_capita, df_sector = load_co2_data("datasets/co2_data")
    df_events = load_events_data(
        "datasets/Top_20_GDP_CO2_Events_1970_2022.csv",
    )
    df_land_area = load_land_area_data(
        "datasets/land_area_data/API_AG.LND.TOTL.K2_DS2_en_csv_v2_323.csv",
    )
    df_gdp_growth = load_gdp_data(
        "datasets/gdp_data/API_NY.GDP.MKTP.KD.ZG_DS2_en_csv_v2_40824.csv",
    )
except FileNotFoundError as e:
    st.error(f"Data file not found: {e}.  Please ensure all dataset files are present.")
    st.stop()


# =============================================================================
# 3. SIDEBAR — Filters & Presets
# =============================================================================

with st.sidebar:
    st.title("\U0001F30D CO2 Dashboard")
    st.caption("Explore global emissions across countries, sectors, and time.")

    # ── Time range slider ────────────────────────────────────────────────────
    st.header("Time Range")
    min_y = int(df_totals["Year"].min())
    max_y = int(df_totals["Year"].max())
    year_range: tuple[int, int] = st.slider(
        "Select period", min_y, max_y, (1970, max_y),
    )

    st.divider()

    # ── Country selection with preset groups ─────────────────────────────────
    st.header("Country Selection")
    available_countries: list[str] = sorted(df_totals["Country"].unique())

    def _on_preset_change():
        """Callback: when the preset dropdown changes, push the corresponding
        country list into the multiselect's session-state key."""
        choice = st.session_state["preset_key"]
        if choice != "Custom":
            st.session_state["country_ms"] = [
                c for c in COUNTRY_PRESETS[choice] if c in available_countries
            ]

    preset_choice = st.selectbox(
        "Choose a Group",
        list(COUNTRY_PRESETS.keys()),
        index=0,
        key="preset_key",
        on_change=_on_preset_change,
    )

    # Provide a sensible default only on the very first render
    if "country_ms" not in st.session_state:
        initial_default = [
            c for c in ["United States", "China", "India"]
            if c in available_countries
        ]
    else:
        initial_default = st.session_state["country_ms"]

    selected_countries: list[str] = st.multiselect(
        "Select Specific Countries",
        available_countries,
        default=initial_default,
        key="country_ms",
    )

    st.divider()
    st.caption(f"**{len(selected_countries)}** countries selected")

    # ── Timeline Settings ─────────────────────────────────────────────────
    st.header("\U0001F4C5 Timeline")
    show_events = st.checkbox(
        "Show Historic Events", value=False, key="evt_global",
    )
    if show_events:
        categories = sorted(df_events["Country"].unique())
        evt_cats = st.multiselect(
            "Filter by origin", categories, default=categories,
            key="evt_cats_global",
        )
    else:
        evt_cats = []

# Guard: nothing to show without at least one country
if not selected_countries:
    st.warning("Please select at least one country to view the dashboard.")
    st.stop()


# =============================================================================
# 4. FILTER DATA
# =============================================================================

mask_totals = (
    df_totals["Country"].isin(selected_countries)
    & df_totals["Year"].between(*year_range)
)
df_t_filtered = df_totals[mask_totals]

latest_year: int = (
    int(df_t_filtered["Year"].max()) if not df_t_filtered.empty else year_range[1]
)

mask_capita = (
    df_capita["Country"].isin(selected_countries)
    & df_capita["Year"].between(*year_range)
)
df_c_filtered = df_capita[mask_capita]

mask_sector = (
    df_sector["Country"].isin(selected_countries)
    & df_sector["Year"].between(*year_range)
)
df_s_filtered = df_sector[mask_sector]


# =============================================================================
# 5. DASHBOARD HEADER & TABS
# =============================================================================

st.title("CO2 Emissions Analysis Dashboard")

tab1, tab2, tab3 = st.tabs([
    "\U0001F30D  The Big Picture",
    "\U0001F4B0  Equity & Economy",
    "\U0001F3ED  Sectoral Deep Dive",
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — THE BIG PICTURE
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    render_tab1_charts(
        df_t_filtered=df_t_filtered,
        df_land_area=df_land_area,
        df_events=df_events,
        selected_countries=selected_countries,
        year_range=year_range,
        latest_year=latest_year,
        show_events=show_events,
        evt_cats=evt_cats,
    )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — EQUITY & ECONOMY
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    render_tab2_charts(
        df_t_filtered=df_t_filtered,
        df_c_filtered=df_c_filtered,
        df_totals=df_totals,
        df_gdp_growth=df_gdp_growth,
        df_events=df_events,
        selected_countries=selected_countries,
        year_range=year_range,
        show_events=show_events,
        evt_cats=evt_cats,
    )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — SECTORAL DEEP DIVE
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    render_tab3_charts(
        df_s_filtered=df_s_filtered,
        df_events=df_events,
        selected_countries=selected_countries,
        year_range=year_range,
        latest_year=latest_year,
        show_events=show_events,
        evt_cats=evt_cats,
    )


# =============================================================================
# 6. FOOTER
# =============================================================================
st.divider()
st.caption(
    "Data: [EDGAR v8.0](https://edgar.jrc.ec.europa.eu/) · "
    "[World Bank Open Data](https://data.worldbank.org/)  —  "
    "Built with Streamlit & Plotly"
)
