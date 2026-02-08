"""
Configuration and Constants
============================
Centralized configuration for the CO2 Dashboard including color palettes,
chart settings, and country group presets.
"""

# =============================================================================
# COLOUR PALETTES & CHART SETTINGS
# =============================================================================

# 12-colour qualitative palette designed for climate/environment charts.
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

PLOTLY_TEMPLATE = "plotly_white"
CHART_MARGIN = dict(l=50, r=30, t=30, b=50)


# =============================================================================
# COUNTRY PRESETS
# =============================================================================

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
# CUSTOM CSS
# =============================================================================

CUSTOM_CSS = """
<style>    
    /* Heading typography */
    h1 { font-weight: 800 !important; letter-spacing: -0.5px; }
    h2, h3 { font-weight: 700 !important; }

    /* Metric cards — bigger values, uppercase labels */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Tab strip — rounded tops, bold labels */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 6px 6px 0 0;
        font-weight: 600;
    }

    @media (prefers-color-scheme: light) {
        
        /* Page background — light sage */
        .main { background-color: #f0f4f3; }

        /* Heading Colors — Dark Teal */
        h1 { color: #1B5E4B !important; }
        h2, h3 { color: #2E8B57 !important; }

        /* Metric Colors */
        [data-testid="stMetricValue"] { color: #1B5E4B !important; }
        [data-testid="stMetricLabel"] { color: #5a7d6e !important; }

        /* Sidebar — pale green backdrop */
        [data-testid="stSidebar"] { background-color: #e8f0ec; }
        [data-testid="stSidebar"] h1 { color: #1B5E4B !important; }

        /* Soft dividers */
        hr { border-color: #c5d8cf !important; }
    }
</style>
"""
