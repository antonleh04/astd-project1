"""
Data Loading Module
===================
Functions for loading and preprocessing CO2, GDP, land area, and events data.
"""

import streamlit as st
import pandas as pd


# =============================================================================
# ISO CODE MAPPING
# =============================================================================

@st.cache_data
def get_country_iso_mapping() -> dict[str, str]:
    """Return a lookup table that maps country/event names to ISO codes.
    Used for events data which doesn't have ISO codes."""
    return {
        # Events data mappings
        "Global": "GLOBAL",
        "World": "GLOBAL",
        "United States": "USA",
        "China": "CHN",
        "Germany": "DEU",
        "Japan": "JPN",
        "United Kingdom": "GBR",
        "France": "FRA",
        "Italy": "ITA",
        "India": "IND",
        "Russia": "RUS",
        "Brazil": "BRA",
        "Canada": "CAN",
        "Australia": "AUS",
        "South Korea": "KOR",
        "Mexico": "MEX",
        "Spain": "ESP",
        "Indonesia": "IDN",
        "Netherlands": "NLD",
        "Saudi Arabia": "SAU",
        "Turkey": "TUR",
        "Switzerland": "CHE",
        "Poland": "POL",
        "Belgium": "BEL",
        "Sweden": "SWE",
        "Iran": "IRN",
        "Austria": "AUT",
        "Norway": "NOR",
        "United Arab Emirates": "ARE",
        "Argentina": "ARG",
        "South Africa": "ZAF",
        "Denmark": "DNK",
        "Thailand": "THA",
        "Malaysia": "MYS",
        "Singapore": "SGP",
        "Israel": "ISR",
        "Hong Kong": "HKG",
        "Finland": "FIN",
        "Chile": "CHL",
        "Portugal": "PRT",
        "Greece": "GRC",
        "Czech Republic": "CZE",
        "Czechia": "CZE",
        "Romania": "ROU",
        "Vietnam": "VNM",
        "New Zealand": "NZL",
        "Iraq": "IRQ",
        "Kuwait": "KWT",
        "Qatar": "QAT",
        "Kazakhstan": "KAZ",
        "Ukraine": "UKR",
        "Egypt": "EGY",
        "Pakistan": "PAK",
        "Philippines": "PHL",
        "Algeria": "DZA",
        "Colombia": "COL",
        "Bangladesh": "BGD",
        "Hungary": "HUN",
        "Slovakia": "SVK",
        "Bulgaria": "BGR",
        "Croatia": "HRV",
        "Lithuania": "LTU",
        "Slovenia": "SVN",
        "Latvia": "LVA",
        "Estonia": "EST",
        "Luxembourg": "LUX",
        "Cyprus": "CYP",
        "Malta": "MLT",
        "Ireland": "IRL",
        "Bahrain": "BHR",
        "Brunei": "BRN",
        "North Korea": "PRK",
    }


def add_iso_codes_to_events(df: pd.DataFrame) -> pd.DataFrame:
    """Add ISO codes to events dataframe based on country names."""
    iso_mapping = get_country_iso_mapping()
    df["ISOcode"] = df["Country"].map(lambda x: iso_mapping.get(x, x))
    return df


# =============================================================================
# DATA LOADERS
# =============================================================================

@st.cache_data
def load_events_data(file_path: str) -> pd.DataFrame:
    """Load curated climate/economic events CSV and add ISO codes."""
    df = pd.read_csv(file_path)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df.dropna(subset=["Year"], inplace=True)
    df["Year"] = df["Year"].astype(int)
    return add_iso_codes_to_events(df)


@st.cache_data
def load_co2_data(co2_data_dir: str):
    """Load and melt the three EDGAR CO2 CSVs (totals, per-capita, by-sector).
    Returns a tuple of three DataFrames."""
    df_totals = pd.read_csv(f"{co2_data_dir}/fossil_CO2_totals_by_country.csv").melt(
        id_vars=["ISOcode", "Country"], var_name="Year", value_name="CO2",
    )
    df_capita = pd.read_csv(f"{co2_data_dir}/fossil_CO2_per_capita_by_country.csv").melt(
        id_vars=["ISOcode", "Country"], var_name="Year", value_name="CO2_per_capita",
    )
    df_sector = pd.read_csv(f"{co2_data_dir}/fossil_CO2_by_sector_and_country.csv").melt(
        id_vars=["Sector", "ISOcode", "Country"], var_name="Year", value_name="CO2",
    )
    # Coerce year columns and drop invalid rows
    for df in [df_totals, df_capita, df_sector]:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        df.dropna(subset=["Year"], inplace=True)
        df["Year"] = df["Year"].astype(int)
    return df_totals, df_capita, df_sector


@st.cache_data
def load_land_area_data(file_path: str) -> pd.DataFrame:
    """Load World Bank land-area indicator and melt from wide to long format."""
    df = pd.read_csv(file_path, skiprows=4)
    df = df.melt(
        id_vars=["Country Name", "Country Code", "Indicator Name", "Indicator Code"],
        var_name="Year", value_name="Land area (sq. km)",
    )
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df.dropna(subset=["Year"], inplace=True)
    df["Year"] = df["Year"].astype(int)
    df.rename(columns={"Country Name": "Country", "Country Code": "ISOcode"}, inplace=True)
    df["Land area (sq. km)"] = pd.to_numeric(df["Land area (sq. km)"], errors="coerce")
    return df


@st.cache_data
def load_gdp_data(file_path: str) -> pd.DataFrame:
    """Load World Bank GDP-growth indicator and melt from wide to long format."""
    df = pd.read_csv(file_path, skiprows=4)
    df = df.melt(
        id_vars=["Country Name", "Country Code", "Indicator Name", "Indicator Code"],
        var_name="Year", value_name="GDP Growth (annual %)",
    )
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df.dropna(subset=["Year"], inplace=True)
    df["Year"] = df["Year"].astype(int)
    df.rename(columns={"Country Name": "Country", "Country Code": "ISOcode"}, inplace=True)
    df["GDP Growth (annual %)"] = pd.to_numeric(
        df["GDP Growth (annual %)"], errors="coerce",
    )
    return df
