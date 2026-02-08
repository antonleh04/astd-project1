"""
Data Loading Module
===================
Functions for loading and preprocessing CO2, GDP, land area, and events data.
"""

import streamlit as st
import pandas as pd


# =============================================================================
# DATA LOADERS
# =============================================================================

@st.cache_data
def load_events_data(file_path: str) -> pd.DataFrame:
    """Load curated climate/economic events CSV with ISO codes."""
    df = pd.read_csv(file_path)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df.dropna(subset=["Year"], inplace=True)
    df["Year"] = df["Year"].astype(int)
    return df


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
