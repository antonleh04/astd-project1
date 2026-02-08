# Project Structure

The code has been refactored into a modular structure for better maintainability and organization.

## File Organization

```
astd-project1/
├── app.py                          # Main entry point - Streamlit UI and orchestration
├── config.py                       # Configuration, constants, color palettes, CSS
├── data_loader.py                  # Data loading and preprocessing functions
├── utils.py                        # Utility functions (event filtering, annotations)
├── visualizations/                 # Visualization modules organized by tab
│   ├── __init__.py                # Package initialization
│   ├── tab1_charts.py             # Tab 1: The Big Picture visualizations
│   ├── tab2_charts.py             # Tab 2: Equity & Economy visualizations
│   └── tab3_charts.py             # Tab 3: Sectoral Deep Dive visualizations
├── datasets/                       # Data files (unchanged)
├── app_old.py                      # Backup of original monolithic file
└── STRUCTURE.md                    # This file

```

## Module Descriptions

### `app.py` (Main Application)
- **Purpose**: Entry point for the Streamlit dashboard
- **Responsibilities**:
  - Page configuration and CSS injection
  - Data loading orchestration
  - Sidebar controls (filters, country selection, event toggles)
  - Data filtering based on user selections
  - Tab structure and rendering coordination
- **Size**: ~250 lines (down from ~950 lines)

### `config.py` (Configuration)
- **Purpose**: Centralized configuration and constants
- **Contains**:
  - `CLIMATE_QUALITATIVE`: 12-color palette for charts
  - `PLOTLY_TEMPLATE` and `CHART_MARGIN`: Chart styling constants
  - `COUNTRY_PRESETS`: Preset country groups (G7, BRICS, EU-27, etc.)
  - `CUSTOM_CSS`: Streamlit custom styling

### `data_loader.py` (Data Management)
- **Purpose**: Data loading and preprocessing
- **Functions**:
  - `get_country_name_mapping()`: Country name standardization lookup
  - `normalize_country_names()`: Apply name mapping to DataFrames
  - `load_co2_data()`: Load CO2 totals, per-capita, and sector data
  - `load_events_data()`: Load historic events CSV
  - `load_land_area_data()`: Load World Bank land area data
  - `load_gdp_data()`: Load World Bank GDP growth data
- **Features**: All loaders use `@st.cache_data` for performance

### `utils.py` (Utilities)
- **Purpose**: Helper functions for event handling
- **Functions**:
  - `filter_events()`: Filter events by country and year range
  - `add_events_to_fig()`: Add staggered event annotations to Plotly charts

### `visualizations/` (Chart Modules)

#### `tab1_charts.py` - The Big Picture
- **Visualizations**:
  - KPI metrics (4 cards: Latest Total, Avg Emission, Variance, Countries)
  - Emissions Trend Over Time (line chart with optional historic events)
  - Emissions Treemap by Land Area (log-scale colored treemap)

#### `tab2_charts.py` - Equity & Economy
- **Visualizations**:
  - Emissions Trajectory (per-capita vs total with start/end markers)
  - Cross-Correlation Analysis:
    - Dual-axis time series (CO2 YoY Change vs GDP Growth)
    - CCF lollipop chart with automatic peak interpretation

#### `tab3_charts.py` - Sectoral Deep Dive
- **Visualizations**:
  - Sector Composition Over Time (stacked area chart)
  - Sectoral Fingerprint Treemap (country/sector breakdown)

## Benefits of Refactoring

1. **Separation of Concerns**: Each module has a single, clear responsibility
2. **Maintainability**: Easier to locate and modify specific functionality
3. **Testability**: Individual modules can be tested in isolation
4. **Readability**: Smaller files are easier to understand
5. **Reusability**: Data loading and utility functions can be reused
6. **Scalability**: Easy to add new tabs or visualizations

## Running the Application

The application runs exactly as before:

```bash
streamlit run app.py
```

All functionality is preserved; only the code organization has changed.

## Migration Notes

- Original monolithic file backed up as `app_old.py`
- No changes to data files or directory structure
- All imports use relative imports within the package
- Streamlit caching decorators preserved for performance
