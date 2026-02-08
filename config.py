"""
Configuration and Constants
============================
Centralized configuration for the CO2 Dashboard including color palettes,
chart settings, and country group presets.
"""

CLIMATE_QUALITATIVE: list[str] = [
    "#1B5E4B",
    "#E85D3A",
    "#2E8B57",
    "#D4A843",
    "#4A90D9",
    "#8B5E3C",
    "#6A5ACD",
    "#20B2AA",
    "#CD5C5C",
    "#708090",
    "#DAA520",
    "#2F4F4F",
]

COLORS = {
    "co2_change": "#E85D3A",
    "gdp_growth": "#4A90D9",
    "positive": "#2E8B57",
    "negative": "#E85D3A",
    "neutral": "#708090",
    "global_event": "#4A90D9",
    "local_event": "#E85D3A",
    "stem_line": "#c5d8cf",
    "zero_line": "#708090",
}

PLOTLY_TEMPLATE = "plotly_white"
CHART_MARGIN = dict(l=50, r=30, t=30, b=50)


COUNTRY_PRESETS: dict[str, list[str]] = {
    "Custom": [],
    "G7": ["USA", "GBR", "FRA", "DEU", "JPN", "CAN", "ITA"],
    "BRICS": ["BRA", "RUS", "IND", "CHN", "ZAF"],
    "EU-27": [
        "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "AUT", "POL",
        "SWE", "DNK", "FIN", "IRL", "PRT", "GRC", "CZE", "ROU",
        "HUN", "SVK", "BGR", "HRV", "LTU", "SVN", "LVA", "EST",
        "LUX", "CYP", "MLT",
    ],
    "Top 10 Emitters": [
        "CHN", "USA", "IND", "RUS", "JPN", "DEU", "KOR", "IRN", "SAU", "CAN",
    ],
    "Top 5 Per Capita": ["QAT", "KWT", "ARE", "BHR", "BRN"],
}


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
