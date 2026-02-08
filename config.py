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

# Semantic color aliases for specific use cases across charts
COLORS = {
    # Data series
    "co2_change": "#E85D3A",     # warm red-orange for CO2/emissions changes
    "gdp_growth": "#4A90D9",     # steel blue for economic indicators
    # Value judgements
    "positive": "#2E8B57",       # sea green for positive/good values
    "negative": "#E85D3A",       # red-orange for negative/bad values
    "neutral": "#708090",        # slate grey for neutral elements
    # Event annotations
    "global_event": "#4A90D9",   # blue for global events
    "local_event": "#E85D3A",    # red-orange for country-specific events
    # Chart elements
    "stem_line": "#c5d8cf",      # light color for lollipop chart stems
    "zero_line": "#708090",      # slate grey for zero reference lines
}

PLOTLY_TEMPLATE = "plotly_white"
CHART_MARGIN = dict(l=50, r=30, t=30, b=50)


# =============================================================================
# COUNTRY PRESETS (Using ISO Codes)
# =============================================================================

COUNTRY_PRESETS: dict[str, list[str]] = {
    "Custom": [],
    "G7": [
        "USA",  # United States
        "GBR",  # United Kingdom
        "FRA",  # France and Monaco
        "DEU",  # Germany
        "JPN",  # Japan
        "CAN",  # Canada
        "ITA",  # Italy, San Marino and the Holy See
    ],
    "BRICS": [
        "BRA",  # Brazil
        "RUS",  # Russia
        "IND",  # India
        "CHN",  # China
        "ZAF",  # South Africa
    ],
    "EU-27": [
        "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "POL",
        "SWE", "DNK", "FIN", "IRL", "PRT", "GRC", "CZE", "ROU",
        "HUN", "SVK", "BGR", "HRV", "LTU", "SVN", "LVA", "EST",
        "LUX", "CYP", "MLT",
    ],
    "Top 10 Emitters": [
        "CHN",  # China
        "USA",  # United States
        "IND",  # India
        "RUS",  # Russia
        "JPN",  # Japan
        "DEU",  # Germany
        "KOR",  # South Korea
        "IRN",  # Iran
        "SAU",  # Saudi Arabia
        "CAN",  # Canada
    ],
    "Top 5 Per Capita": [
        "QAT",  # Qatar
        "KWT",  # Kuwait
        "ARE",  # United Arab Emirates
        "BHR",  # Bahrain
        "BRN",  # Brunei
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


    /* ─── Compact Sidebar Overrides ─── */
    [data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    [data-testid="stSidebar"] h1 {
        font-size: 1.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    [data-testid="stSidebar"] h2 {
        font-size: 1.1rem !important;
        margin-top: 1rem !important;
        margin-bottom: 0.25rem !important;
        padding-top: 0 !important;
    }
    [data-testid="stSidebar"] hr {
        margin: 0.5rem 0 1rem 0 !important;
    }
    [data-testid="stSidebar"] .stRadio > label {
        display: none !important; /* Hide "Show View:" label if redundant */
    }
    
    /* Reduce gap between elements */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        gap: 0.5rem !important;
    }
</style>
"""
