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
  Tab 2 – Equity & Economy   → GDP×CO2 scatter, per-capita heatmap, CCF
  Tab 3 – Sectoral Deep Dive → stacked area, radar, sector drill-down
"""

# ── Imports ──────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from statsmodels.tsa.stattools import ccf   # cross-correlation function


# =============================================================================
# 1. PAGE CONFIG & CSS THEMING
# =============================================================================
# Must be the first Streamlit call in the script.
st.set_page_config(
    page_title="ALLSTAT CO2 Dashboard",
    layout="wide",
    page_icon="\U0001F30D",
)

# Inject custom CSS to override Streamlit defaults with a climate-focused
# colour scheme (dark teal headings, soft green sidebar, muted dividers).
st.markdown("""
<style>
    /* Page background — light sage */
    .main { background-color: #f0f4f3; }

    /* Heading hierarchy */
    h1 { color: #1B5E4B !important; font-weight: 800 !important; letter-spacing: -0.5px; }
    h2, h3 { color: #2E8B57 !important; font-weight: 700 !important; }

    /* Metric cards — prominent values with upper-case labels */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #1B5E4B !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #5a7d6e !important;
    }

    /* Sidebar — pale green backdrop */
    [data-testid="stSidebar"] { background-color: #e8f0ec; }
    [data-testid="stSidebar"] h1 { font-size: 22px !important; color: #1B5E4B !important; }

    /* Tab strip — rounded tops, bold labels */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 6px 6px 0 0;
        font-weight: 600;
    }

    /* Soft dividers */
    hr { border-color: #c5d8cf !important; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 2. COLOUR PALETTES & CONSTANTS
# =============================================================================

# 12-colour qualitative palette designed for climate/environment charts.
# Avoids pure-rainbow look; ordered so the first few colours are distinct.
CLIMATE_QUALITATIVE: list[str] = [
    "#1B5E4B",  # deep teal
    "#E85D3A",  # warm red-orange
    "#2E8B57",  # sea green
    "#D4A843",  # gold
    "#4A90D9",  # steel blue
    "#8B5E3C",  # brown
    "#6A5ACD",  # slate blue
    "#20B2AA",  # light sea green
    "#CD5C5C",  # indian red
    "#708090",  # slate grey
    "#DAA520",  # goldenrod
    "#2F4F4F",  # dark slate
]

PLOTLY_TEMPLATE = "plotly_white"      # clean background for every chart
CHART_MARGIN = dict(l=50, r=30, t=30, b=50)  # default chart margins


# =============================================================================
# 3. COUNTRY PRESETS
# =============================================================================
# Each key maps to a list of country names as they appear in the CO2 dataset
# (after normalisation).  "Custom" leaves the multiselect unchanged.

COUNTRY_PRESETS: dict[str, list[str]] = {
    "Custom": [],
    "G7": [
        "United States", "United Kingdom", "France and Monaco",
        "Germany", "Japan", "Canada",
        "Italy, San Marino and the Holy See",
    ],
    "BRICS": [
        "Brazil", "Russia", "India", "China", "South Africa",
    ],
    "EU-27": [
        "Germany", "France and Monaco", "Italy, San Marino and the Holy See",
        "Spain and Andorra", "Netherlands", "Belgium", "Austria", "Poland",
        "Sweden", "Denmark", "Finland", "Ireland", "Portugal", "Greece",
        "Czechia", "Romania", "Hungary", "Slovakia", "Bulgaria", "Croatia",
        "Lithuania", "Slovenia", "Latvia", "Estonia", "Luxembourg", "Cyprus",
        "Malta",
    ],
    "Top 10 Emitters": [
        "China", "United States", "India", "Russia", "Japan",
        "Germany", "South Korea", "Iran", "Saudi Arabia", "Canada",
    ],
    "Top 5 Per Capita": [
        "Qatar", "Kuwait", "United Arab Emirates", "Bahrain", "Brunei",
    ],
}


# =============================================================================
# 4. DATA LOADING
# =============================================================================
# Every loader is cached with @st.cache_data so CSVs are parsed only once per
# session.  World Bank datasets use `skiprows=4` to skip their metadata header.

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


@st.cache_data
def load_events_data(file_path: str) -> pd.DataFrame:
    """Load curated climate/economic events CSV and normalise country names."""
    df = pd.read_csv(file_path)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df.dropna(subset=["Year"], inplace=True)
    df["Year"] = df["Year"].astype(int)
    return normalize_country_names(df, "Country")


@st.cache_data
def load_data(co2_data_dir: str):
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


# =============================================================================
# 5. EVENT HELPERS
# =============================================================================
# Events are shown as vertical dotted lines with colour-coded annotations on
# whatever chart the user enables them for.  Global events are blue; local
# (country-specific) events are red-orange.

def filter_events(
    events_df: pd.DataFrame,
    selected_countries: list[str],
    year_range: tuple[int, int],
) -> pd.DataFrame:
    """Return events that are either global or belong to one of the selected
    countries and fall within the chosen year range."""
    global_mask = events_df["Country"].isin(["Global", "World"])
    local_mask  = events_df["Country"].isin(selected_countries)
    year_mask   = events_df["Year"].between(*year_range)
    return events_df[(global_mask | local_mask) & year_mask]


def add_events_to_fig(
    fig: go.Figure,
    events_df: pd.DataFrame,
    selected_countries: list[str],
    year_range: tuple[int, int],
) -> None:
    """Overlay staggered, colour-coded event annotations on a Plotly figure.
    Annotations cycle through five vertical offsets to reduce overlap."""
    filtered = filter_events(events_df, selected_countries, year_range)
    if filtered.empty:
        return

    # Stagger annotations vertically so they don't pile up
    y_positions = [0.95, 0.85, 0.75, 0.65, 0.55]

    for i, (_, event) in enumerate(filtered.iterrows()):
        is_global  = event["Country"] in ["Global", "World"]
        icon       = "\U0001F30D" if is_global else "\U0001F4CD"
        line_color = "#4A90D9" if is_global else "#E85D3A"
        y_ref      = y_positions[i % len(y_positions)]

        fig.add_vline(
            x=event["Year"], line_width=1.2, line_dash="dot",
            line_color=line_color, opacity=0.55,
        )
        fig.add_annotation(
            x=event["Year"], y=y_ref, yref="paper",
            text=f"{icon} {event['Event']}",
            showarrow=True, arrowhead=2, arrowsize=0.8,
            arrowwidth=1, arrowcolor=line_color,
            ax=20, ay=-20,
            font=dict(size=9, color=line_color),
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor=line_color, borderwidth=1, borderpad=3,
            hovertext=(
                f"<b>{event['Event']} ({event['Year']})</b><br>"
                f"<i>{event['Country']}</i><br>{event['Description']}"
            ),
        )


def render_event_controls(tab_key: str, events_df: pd.DataFrame):
    """Render an expander with a toggle + multiselect for historic events.
    Returns ``(show_events: bool, selected_origins: list[str])``."""
    with st.expander("\U0001F4C5 Timeline Settings", expanded=False):
        c1, c2 = st.columns([1, 2])
        with c1:
            show = st.checkbox(
                "Show Historic Events", value=False, key=f"evt_{tab_key}",
            )
        with c2:
            categories = sorted(events_df["Country"].unique())
            sel_cats = st.multiselect(
                "Filter by origin", categories, default=categories,
                key=f"evt_cats_{tab_key}", disabled=not show,
            )
    return show, sel_cats


# =============================================================================
# 6. LOAD ALL DATASETS
# =============================================================================

try:
    df_totals, df_capita, df_sector = load_data("datasets/co2_data")
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
# 7. SIDEBAR — Filters & Presets
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
        country list into the multiselect's session-state key so that the
        widget reflects the new selection immediately."""
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
# 8. FILTER DATA
# =============================================================================
# Apply the sidebar selections (countries + year range) to each dataset once,
# so every tab works with pre-filtered DataFrames.

mask_totals = (
    df_totals["Country"].isin(selected_countries)
    & df_totals["Year"].between(*year_range)
)
df_t_filtered = df_totals[mask_totals]

# The "latest year" is the most recent year present in the filtered totals
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
# 9. DASHBOARD HEADER & TABS
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

    # ── KPI Metrics Row ──────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)

    avg_emissions = df_t_filtered["CO2"].mean()
    variance      = df_t_filtered["CO2"].var() if len(df_t_filtered) > 1 else 0

    latest_total = df_t_filtered[df_t_filtered["Year"] == latest_year]["CO2"].sum()
    prev_total   = df_t_filtered[df_t_filtered["Year"] == latest_year - 1]["CO2"].sum()
    yoy = ((latest_total - prev_total) / prev_total * 100) if prev_total else 0

    # delta_color="inverse" → green when emissions decrease (good for climate)
    m1.metric(
        "Latest Total", f"{latest_total:,.0f} Mt", f"{yoy:+.1f}% YoY",
        delta_color="inverse",
    )
    m2.metric("Avg Emission", f"{avg_emissions:,.1f} Mt")
    m3.metric("Variance", f"{variance:,.2e}")
    m4.metric("Countries", len(selected_countries))

    st.divider()

    # ── Emissions trend (line chart) ─────────────────────────────────────────
    st.subheader("Emissions Trend Over Time")

    fig_trend = go.Figure()
    for idx, country in enumerate(selected_countries):
        df_c = df_t_filtered[df_t_filtered["Country"] == country].sort_values("Year")
        color = CLIMATE_QUALITATIVE[idx % len(CLIMATE_QUALITATIVE)]
        # Use markers only when there are few countries to keep the chart readable
        mode = "lines+markers" if len(selected_countries) < 10 else "lines"
        fig_trend.add_trace(go.Scatter(
            x=df_c["Year"], y=df_c["CO2"],
            mode=mode, name=country,
            line=dict(color=color, width=2.2),
            marker=dict(size=4),
            hovertemplate=(
                f"<b>{country}</b><br>"
                "Year: %{x}<br>"
                "CO2: %{y:,.2f} Mt<extra></extra>"
            ),
        ))

    fig_trend.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis_title="Year",
        yaxis_title="CO2 Emissions (Mt)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=480,
        margin=CHART_MARGIN,
    )

    # Overlay historic events if the user toggled them on
    if show_events:
        events_sub = df_events[df_events["Country"].isin(evt_cats)]
        add_events_to_fig(fig_trend, events_sub, selected_countries, year_range)

    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    # ── Treemap: land area sized, CO2 coloured ──────────────────────────────
    st.subheader(f"Emissions Treemap by Land Area ({latest_year})")
    st.caption(
        "Each rectangle is proportional to the country's land area; the colour "
        "intensity shows CO2 emissions on a **log scale**."
    )

    df_land_latest = df_land_area[
        (df_land_area["Year"] == latest_year)
        & (df_land_area["Country"].isin(selected_countries))
    ]
    df_co2_latest = df_t_filtered[df_t_filtered["Year"] == latest_year]

    df_tree = pd.merge(
        df_co2_latest[["Country", "CO2"]],
        df_land_latest[["Country", "Land area (sq. km)"]],
        on="Country", how="inner",
    ).dropna(subset=["Land area (sq. km)", "CO2"])

    if df_tree.empty:
        st.info("No matching land-area data for the selected countries / year.")
    else:
        df_tree["CO2_log"] = np.log10(df_tree["CO2"].clip(lower=1))
        fig_treemap = px.treemap(
            df_tree,
            path=["Country"],
            values="Land area (sq. km)",
            color="CO2_log",
            color_continuous_scale="YlOrRd",
            hover_data={"CO2": ":.2f", "CO2_log": False},
            labels={"CO2_log": "CO2 (log)"},
        )
        fig_treemap.update_coloraxes(
            colorbar_title_text="CO2 (Mt, log\u2081\u2080)",
            colorbar_tickmode="array",
            colorbar_tickvals=np.log10([1, 10, 100, 1000, 10000]),
            colorbar_ticktext=["1", "10", "100", "1 k", "10 k"],
        )
        fig_treemap.update_layout(
            template=PLOTLY_TEMPLATE,
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_treemap, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — EQUITY & ECONOMY
# ─────────────────────────────────────────────────────────────────────────────
with tab2:

    # ── GDP vs CO2 scatter (bubble chart) ────────────────────────────────────
    st.subheader("CO2 Emissions vs. GDP Growth")
    st.caption(
        "Bubble size reflects total emissions — look for countries that decouple "
        "economic growth from CO2 output."
    )

    # Determine the overlapping year range between CO2 and GDP data
    min_gdp_year = max(
        int(df_t_filtered["Year"].min()) if not df_t_filtered.empty else year_range[0],
        int(df_gdp_growth["Year"].min()),
    )
    max_gdp_year = min(
        int(df_t_filtered["Year"].max()) if not df_t_filtered.empty else year_range[1],
        int(df_gdp_growth["Year"].max()),
    )

    if min_gdp_year > max_gdp_year:
        st.warning("No overlapping years for CO2 and GDP data with current filters.")
    else:
        # Build merged CO2 × GDP data for ALL years in the overlapping range
        gdp_years_range = range(min_gdp_year, max_gdp_year + 1)
        df_co2_all = df_totals[
            (df_totals["Country"].isin(selected_countries))
            & (df_totals["Year"].isin(gdp_years_range))
        ]
        df_gdp_all = df_gdp_growth[
            (df_gdp_growth["Country"].isin(selected_countries))
            & (df_gdp_growth["Year"].isin(gdp_years_range))
        ]
        df_merged = pd.merge(
            df_co2_all, df_gdp_all, on=["Country", "Year"], how="inner",
        ).dropna(subset=["CO2", "GDP Growth (annual %)"])

        if df_merged.empty:
            st.info("No combined data for selected countries in the available year range.")
        else:
            # Sort by year so the animation plays chronologically
            df_merged = df_merged.sort_values("Year")
            # Compute global axis limits so the view stays stable across frames
            x_max = df_merged["CO2"].max() * 1.10
            y_min = df_merged["GDP Growth (annual %)"].min() * 1.15
            y_max = df_merged["GDP Growth (annual %)"].max() * 1.15

            fig_scatter = px.scatter(
                df_merged,
                x="CO2", y="GDP Growth (annual %)",
                color="Country", hover_name="Country",
                size="CO2", size_max=40,
                animation_frame="Year", animation_group="Country",
                color_discrete_sequence=CLIMATE_QUALITATIVE,
                range_x=[0, x_max],
                range_y=[y_min, y_max],
                hover_data={
                    "Year": True,
                    "CO2": ":.2f",
                    "GDP Growth (annual %)": ":.2f",
                },
            )
            fig_scatter.update_layout(
                template=PLOTLY_TEMPLATE,
                xaxis_title="CO2 Emissions (Mt)",
                yaxis_title="GDP Growth (Annual %)",
                height=520,
                margin=CHART_MARGIN,
            )
            # Slow down animation for readability
            fig_scatter.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 600
            fig_scatter.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300
            st.plotly_chart(fig_scatter, use_container_width=True)

    st.divider()

    # ── Per-capita emissions: Heatmap + Animated bar race ────────────────────
    st.subheader("Per-Capita Emissions")
    col_heat, col_race = st.columns(2)

    with col_heat:
        st.markdown("##### Heatmap")
        if not df_c_filtered.empty:
            pivot = df_c_filtered.pivot(
                index="Country", columns="Year", values="CO2_per_capita",
            )
            fig_heat = px.imshow(
                pivot,
                color_continuous_scale="Tealgrn",
                aspect="auto",
                labels=dict(color="t CO2 / capita"),
            )
            fig_heat.update_layout(
                template=PLOTLY_TEMPLATE,
                height=480,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("No per-capita data available.")

    with col_race:
        st.markdown("##### Top 10 Emitters Race")
        # Keep only the top-10 per year to make the animation readable
        df_race = df_c_filtered.sort_values(
            ["Year", "CO2_per_capita"], ascending=[True, False],
        )
        df_race = df_race.groupby("Year").head(10).reset_index(drop=True)

        if not df_race.empty:
            x_limit = df_race["CO2_per_capita"].max() * 1.15
            fig_race = px.bar(
                df_race,
                x="CO2_per_capita", y="Country", color="Country",
                animation_frame="Year", animation_group="Country",
                orientation="h", range_x=[0, x_limit],
                color_discrete_sequence=CLIMATE_QUALITATIVE,
                labels={"CO2_per_capita": "Tonnes / Capita"},
            )
            fig_race.update_layout(
                template=PLOTLY_TEMPLATE,
                yaxis={"categoryorder": "total ascending"},
                height=480,
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            # Slow down the animation a bit for readability
            fig_race.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 600
            st.plotly_chart(fig_race, use_container_width=True)
        else:
            st.info("No race-chart data available.")

    st.divider()

    # ── Cross-Correlation: GDP Growth vs CO2 Change ──────────────────────────
    st.subheader("Cross-Correlation: GDP Growth vs CO2 Change")
    st.caption(
        "Analyse the temporal relationship between economic growth and emissions "
        "changes.  Negative lags mean GDP *leads* CO2; positive lags mean CO2 "
        "changes *precede* GDP."
    )

    # Country picker (skip if only one country selected)
    if len(selected_countries) == 1:
        analysis_country = selected_countries[0]
    else:
        analysis_country = st.selectbox(
            "Select Country for Analysis", selected_countries, key="ccf_country",
        )

    # Build aligned CO2-YoY-change and GDP-growth series
    co2_country = (
        df_totals[df_totals["Country"] == analysis_country][["Year", "CO2"]]
        .sort_values("Year").dropna()
    )
    co2_country["CO2_YoY_Change"] = co2_country["CO2"].pct_change() * 100

    gdp_country = (
        df_gdp_growth[df_gdp_growth["Country"] == analysis_country]
        [["Year", "GDP Growth (annual %)"]]
        .sort_values("Year").dropna()
    )

    merged_ccf = pd.merge(
        co2_country[["Year", "CO2_YoY_Change"]],
        gdp_country[["Year", "GDP Growth (annual %)"]],
        on="Year", how="inner",
    ).dropna()

    if len(merged_ccf) < 10:
        st.warning(
            f"Insufficient data for **{analysis_country}** "
            "(need \u2265 10 overlapping years)."
        )
    else:
        # -- Dual-axis time-series overlay --
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(
            x=merged_ccf["Year"], y=merged_ccf["CO2_YoY_Change"],
            mode="lines+markers", name="CO2 YoY Change (%)",
            line=dict(color="#E85D3A", width=2), marker=dict(size=4),
        ))
        fig_ts.add_trace(go.Scatter(
            x=merged_ccf["Year"], y=merged_ccf["GDP Growth (annual %)"],
            mode="lines+markers", name="GDP Growth (%)",
            line=dict(color="#4A90D9", width=2), marker=dict(size=4),
            yaxis="y2",
        ))
        fig_ts.update_layout(
            template=PLOTLY_TEMPLATE, height=360, hovermode="x unified",
            xaxis=dict(title="Year"),
            yaxis=dict(
                title="CO2 YoY Change (%)",
                title_font=dict(color="#E85D3A"),
                tickfont=dict(color="#E85D3A"),
            ),
            yaxis2=dict(
                title="GDP Growth (%)",
                title_font=dict(color="#4A90D9"),
                tickfont=dict(color="#4A90D9"),
                overlaying="y", side="right",
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
            ),
            margin=dict(l=50, r=50, t=30, b=40),
        )

        if show_events:
            events_sub = df_events[df_events["Country"].isin(evt_cats)]
            add_events_to_fig(fig_ts, events_sub, [analysis_country], year_range)

        st.plotly_chart(fig_ts, use_container_width=True)

        # -- CCF lollipop chart --
        max_possible_lag = min(10, len(merged_ccf) // 3)
        max_lag = st.slider(
            "Max Lag (years)", 1, max_possible_lag,
            min(5, max_possible_lag), key="ccf_lag",
        )

        gdp_series = merged_ccf["GDP Growth (annual %)"].values
        co2_series = merged_ccf["CO2_YoY_Change"].values

        try:
            ccf_pos = ccf(co2_series, gdp_series, adjusted=False)

            # Build symmetric lag array [-max_lag ... +max_lag]
            lags = np.arange(-max_lag, max_lag + 1)
            ccf_subset: list[float] = []
            for lag in lags:
                if lag < 0:
                    # Negative lag: swap the series order
                    ccf_subset.append(
                        ccf(gdp_series, co2_series, adjusted=False)[abs(lag)]
                    )
                else:
                    ccf_subset.append(ccf_pos[lag])

            # Draw stem (stick) for each lag value
            fig_ccf = go.Figure()
            for lag_v, corr_v in zip(lags, ccf_subset):
                fig_ccf.add_trace(go.Scatter(
                    x=[lag_v, lag_v], y=[0, corr_v],
                    mode="lines",
                    line=dict(color="#c5d8cf", width=2),
                    showlegend=False, hoverinfo="skip",
                ))

            # Coloured markers on top of each stem
            colors_ccf = [
                "#E85D3A" if c < 0 else "#2E8B57" for c in ccf_subset
            ]
            fig_ccf.add_trace(go.Scatter(
                x=lags, y=ccf_subset, mode="markers",
                marker=dict(
                    size=12, color=colors_ccf,
                    line=dict(width=1, color="white"),
                ),
                name="Correlation",
                hovertemplate="<b>Lag %{x} yr</b><br>r = %{y:.3f}<extra></extra>",
            ))
            fig_ccf.add_hline(
                y=0, line_dash="dash", line_color="#708090", line_width=1,
            )
            fig_ccf.update_layout(
                template=PLOTLY_TEMPLATE, height=420, showlegend=False,
                xaxis=dict(title="Lag (years)", tickmode="linear", dtick=1),
                yaxis_title="Correlation Coefficient",
                margin=CHART_MARGIN,
            )
            st.plotly_chart(fig_ccf, use_container_width=True)

            # Interpret the peak automatically
            peak_idx  = int(np.argmax(np.abs(ccf_subset)))
            peak_lag  = int(lags[peak_idx])
            peak_corr = ccf_subset[peak_idx]

            if peak_lag == 0:
                interp = (
                    f"**Peak at Lag 0** (r = {peak_corr:.3f}): "
                    "GDP and CO2 changes are **synchronous**."
                )
            elif peak_lag < 0:
                interp = (
                    f"**Peak at Lag {peak_lag}** (r = {peak_corr:.3f}): "
                    f"GDP growth **leads** CO2 by {abs(peak_lag)} year(s)."
                )
            else:
                interp = (
                    f"**Peak at Lag +{peak_lag}** (r = {peak_corr:.3f}): "
                    f"CO2 changes **lead** GDP by {peak_lag} year(s)."
                )
            st.info(interp)

        except Exception as e:
            st.error(f"Cross-correlation error: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — SECTORAL DEEP DIVE
# ─────────────────────────────────────────────────────────────────────────────
with tab3:

    # ── Stacked area: sector composition for one country ─────────────────────
    st.subheader("Sector Composition Over Time")

    if len(selected_countries) == 1:
        focus_country = selected_countries[0]
    else:
        focus_country = st.selectbox(
            "Focus country for stacked area chart",
            selected_countries, key="sector_focus",
        )

    df_focus = df_s_filtered[df_s_filtered["Country"] == focus_country]

    if df_focus.empty:
        st.info(f"No sector data for **{focus_country}** in this range.")
    else:
        sector_ts = df_focus.groupby(["Year", "Sector"])["CO2"].sum().reset_index()
        fig_area = go.Figure()
        sectors = sorted(sector_ts["Sector"].unique())
        for idx, sec in enumerate(sectors):
            df_sec = sector_ts[sector_ts["Sector"] == sec].sort_values("Year")
            color = CLIMATE_QUALITATIVE[idx % len(CLIMATE_QUALITATIVE)]
            fig_area.add_trace(go.Scatter(
                x=df_sec["Year"], y=df_sec["CO2"],
                mode="lines", name=sec, stackgroup="one",
                line=dict(width=0.5, color=color),
                hovertemplate=(
                    f"<b>{sec}</b><br>"
                    "Year: %{x}<br>"
                    "CO2: %{y:,.2f} Mt<extra></extra>"
                ),
            ))
        fig_area.update_layout(
            template=PLOTLY_TEMPLATE,
            title=f"Sectoral Emissions \u2014 {focus_country}",
            xaxis_title="Year",
            yaxis_title="CO2 Emissions (Mt)",
            hovermode="x unified",
            height=460,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
            ),
            margin=dict(l=50, r=30, t=60, b=50),
        )

        if show_events:
            events_sub = df_events[df_events["Country"].isin(evt_cats)]
            add_events_to_fig(fig_area, events_sub, [focus_country], year_range)

        st.plotly_chart(fig_area, use_container_width=True)

    st.divider()

    # ── Radar + Treemap side-by-side ─────────────────────────────────────────
    st.subheader(f"Sectoral Fingerprint ({latest_year})")
    col_radar, col_tree = st.columns(2)

    with col_radar:
        st.markdown("##### Radar Comparison")
        radar_year = st.slider(
            "Year",
            int(df_sector["Year"].min()),
            int(df_sector["Year"].max()),
            int(df_sector["Year"].max()),
            key="radar_yr",
        )
        show_pct = st.toggle("Show as %", value=True, key="radar_pct")

        df_radar = df_sector[
            (df_sector["Year"] == radar_year)
            & (df_sector["Country"].isin(selected_countries))
        ]

        if df_radar.empty:
            st.info("No sector data for selected countries.")
        else:
            df_rg = df_radar.groupby(["Country", "Sector"])["CO2"].sum().reset_index()
            all_sectors = sorted(df_rg["Sector"].unique())

            # Percentage mode: each country's sectors sum to 100 %
            if show_pct:
                totals_map = df_rg.groupby("Country")["CO2"].sum().to_dict()
                df_rg["Value"] = df_rg.apply(
                    lambda r: (r["CO2"] / totals_map[r["Country"]]) * 100
                    if totals_map.get(r["Country"], 0) else 0,
                    axis=1,
                )
            else:
                df_rg["Value"] = df_rg["CO2"]

            fig_radar = go.Figure()
            for idx, country in enumerate(selected_countries):
                df_rc = df_rg[df_rg["Country"] == country]
                if df_rc.empty:
                    continue
                vals = [
                    float(df_rc[df_rc["Sector"] == s]["Value"].iloc[0])
                    if not df_rc[df_rc["Sector"] == s].empty else 0
                    for s in all_sectors
                ]
                color = CLIMATE_QUALITATIVE[idx % len(CLIMATE_QUALITATIVE)]
                fig_radar.add_trace(go.Scatterpolar(
                    r=vals, theta=all_sectors, fill="toself",
                    name=country, line=dict(color=color), opacity=0.4,
                ))

            max_val = df_rg["Value"].max() if not df_rg.empty else 1
            fig_radar.update_layout(
                template=PLOTLY_TEMPLATE,
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, max_val * 1.15]),
                ),
                showlegend=True,
                height=500,
                margin=dict(l=60, r=60, t=40, b=40),
                legend=dict(font=dict(size=10)),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

    with col_tree:
        st.markdown("##### Sector Breakdown Treemap")
        if not df_s_filtered.empty:
            df_sec_tree = df_s_filtered[df_s_filtered["Year"] == latest_year]
            if not df_sec_tree.empty:
                fig_sec_tm = px.treemap(
                    df_sec_tree,
                    path=["Country", "Sector"],
                    values="CO2",
                    color="Sector",
                    color_discrete_sequence=CLIMATE_QUALITATIVE,
                )
                fig_sec_tm.update_layout(
                    template=PLOTLY_TEMPLATE,
                    height=500,
                    margin=dict(l=10, r=10, t=30, b=10),
                )
                st.plotly_chart(fig_sec_tm, use_container_width=True)
            else:
                st.info("No sector data for the latest year.")
        else:
            st.info("No sector data available.")

    st.divider()

    # ── Sector-specific drill-down bar chart ─────────────────────────────────
    st.subheader("Sector Deep Dive")
    if not df_s_filtered.empty:
        sector_list = sorted(df_s_filtered["Sector"].unique())
        selected_sector = st.selectbox("Pick a Sector", sector_list, key="sector_dd")

        sector_df = df_s_filtered[
            (df_s_filtered["Sector"] == selected_sector)
            & (df_s_filtered["Year"] == latest_year)
        ].sort_values("CO2", ascending=False)

        if not sector_df.empty:
            total_co2 = sector_df["CO2"].sum()
            st.metric(
                f"Total {selected_sector} Emissions ({latest_year})",
                f"{total_co2:,.1f} Mt",
            )
            fig_bar = px.bar(
                sector_df,
                x="CO2", y="Country", orientation="h",
                color="CO2", color_continuous_scale="YlOrRd",
                labels={"CO2": "Mt CO2"},
            )
            fig_bar.update_layout(
                template=PLOTLY_TEMPLATE,
                height=max(300, len(sector_df) * 32),
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=10, r=10, t=10, b=40),
            )
            st.plotly_chart(fig_bar, use_container_width=True)


# =============================================================================
# 10. FOOTER
# =============================================================================
st.divider()
st.caption(
    "Data: [EDGAR v8.0](https://edgar.jrc.ec.europa.eu/) \u00b7 "
    "[World Bank Open Data](https://data.worldbank.org/)  \u2014  "
    "Built with Streamlit & Plotly"
)
