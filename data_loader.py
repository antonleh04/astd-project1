"""
Data Loading Module
===================
Functions for loading and preprocessing CO2, GDP, land area, and events data.
"""

import streamlit as st
import pandas as pd


# =============================================================================
# COUNTRY NAME MAPPING
# =============================================================================

@st.cache_data
def get_country_name_mapping() -> dict[str, str]:
    """Return a lookup table that maps common / World Bank country names to the
    naming convention used in the EDGAR CO2 dataset."""
    return {
        "Italy": "Italy, San Marino and the Holy See",
        "Russian Federation": "Russia",
        "France": "France and Monaco",
        "Spain": "Spain and Andorra",
        "Switzerland": "Switzerland and Liechtenstein",
        "Israel": "Israel and Palestine, State of",
        "Korea, Rep.": "South Korea",
        "Korea, Dem. People's Rep.": "North Korea",
        "United States": "United States",
        "United Kingdom": "United Kingdom",
        "China": "China",
        "Germany": "Germany",
        "Japan": "Japan",
        "India": "India",
        "Canada": "Canada",
        "Australia": "Australia",
        "Brazil": "Brazil",
        "Mexico": "Mexico",
        "USA": "United States",
        "US": "United States",
        "United States of America": "United States",
    }


def normalize_country_names(df: pd.DataFrame, country_column: str = "Country") -> pd.DataFrame:
    """Apply the name-mapping table so every dataset shares a consistent
    country-name vocabulary."""
    mapping = get_country_name_mapping()
    df[country_column] = df[country_column].map(lambda x: mapping.get(x, x))
    return df


# =============================================================================
# DATA LOADERS
# =============================================================================

@st.cache_data
def load_events_data(file_path: str) -> pd.DataFrame:
    """Load curated climate/economic events CSV and normalise country names."""
    df = pd.read_csv(file_path)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df.dropna(subset=["Year"], inplace=True)
    df["Year"] = df["Year"].astype(int)
    return normalize_country_names(df, "Country")


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
    df.rename(columns={"Country Name": "Country"}, inplace=True)
    df["Land area (sq. km)"] = pd.to_numeric(df["Land area (sq. km)"], errors="coerce")
    return normalize_country_names(df, "Country")


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
    df.rename(columns={"Country Name": "Country"}, inplace=True)
    df["GDP Growth (annual %)"] = pd.to_numeric(
        df["GDP Growth (annual %)"], errors="coerce",
    )
    return normalize_country_names(df, "Country")
