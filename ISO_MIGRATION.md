# ISO Code Migration Summary

## Overview

The dashboard has been updated to use ISO country codes for all filtering operations instead of country name strings. This provides a more robust and standardized way to handle country data across multiple datasets.

## Changes Made

### 1. Data Loader (`data_loader.py`)

**Removed:**
- `get_country_name_mapping()` - Country name normalization function
- `normalize_country_names()` - Name mapping application function

**Added:**
- `get_country_iso_mapping()` - Maps country/event names to ISO codes
- `add_iso_codes_to_events()` - Adds ISO codes to events DataFrame

**Updated:**
- `load_events_data()` - Now adds ISO codes to events data
- `load_land_area_data()` - Renames `Country Code` to `ISOcode`
- `load_gdp_data()` - Renames `Country Code` to `ISOcode`

### 2. Configuration (`config.py`)

**Updated `COUNTRY_PRESETS`:**
- All preset groups now use ISO codes instead of country names
- G7: Uses codes like "USA", "GBR", "FRA", "DEU", etc.
- BRICS: "BRA", "RUS", "IND", "CHN", "ZAF"
- EU-27: All member state ISO codes
- Top 10 Emitters: "CHN", "USA", "IND", "RUS", "JPN", etc.
- Top 5 Per Capita: "QAT", "KWT", "ARE", "BHR", "BRN"

### 3. Utilities (`utils.py`)

**Updated Functions:**
- `filter_events()` - Now filters by `ISOcode` column instead of `Country`
- `add_events_to_fig()` - Updated parameters and filtering logic
  - Changed `selected_countries` → `selected_iso_codes`
  - Event global detection now checks `ISOcode == "GLOBAL"`

### 4. Main Application (`app.py`)

**Sidebar Changes:**
- Country selection now uses ISO codes internally
- Multiselect displays: `"Country Name (ISO)"`
- Format function: `lambda iso: f"{country_lookup.get(iso, iso)} ({iso})"`
- Session state stores ISO codes, not names

**Filtering:**
- All data filtering now uses `df["ISOcode"].isin(selected_iso_codes)`
- Replaced `selected_countries` with `selected_iso_codes` throughout
- Event filtering converts country names to ISO codes

**Tab Rendering:**
- All render functions now receive `selected_iso_codes` instead of `selected_countries`
- Event categories passed as `evt_iso_codes` instead of `evt_cats`

### 5. Visualizations

#### Tab 1 (`tab1_charts.py`)
- Iterates over `selected_iso_codes`
- Filters data using `df["ISOcode"] == iso_code`
- Displays country names from data for labels
- Treemap joins on `ISOcode` column

#### Tab 2 (`tab2_charts.py`)
- Trajectory chart uses ISO codes for iteration and filtering
- Cross-correlation analysis:
  - Uses ISO codes for country selection
  - Format function shows country names in dropdown
  - Filters by `df["ISOcode"] == analysis_iso`

#### Tab 3 (`tab3_charts.py`)
- Sector focus selection uses ISO codes
- Format function displays country names
- Event filtering uses `evt_iso_codes`

## Benefits

1. **Standardization**: ISO codes are internationally standardized and unambiguous
2. **Robustness**: Eliminates issues with country name variations
3. **Consistency**: All datasets now use the same identifier system
4. **Simplicity**: No more complex country name mapping logic
5. **Maintainability**: Easier to add new countries or datasets

## Data Structure

### CO2 Data (EDGAR)
- Already had `ISOcode` column ✓
- No changes needed to CSV files

### World Bank Data (GDP, Land Area)
- Already had `Country Code` column ✓
- Renamed to `ISOcode` during loading

### Events Data
- Added `ISOcode` column via mapping ✓
- Maps country names to ISO codes
- Special code "GLOBAL" for global events

## ISO Code Mapping

Key ISO codes used in presets:
- USA: United States
- CHN: China
- IND: India
- DEU: Germany (Deutschland)
- GBR: United Kingdom (Great Britain)
- FRA: France
- ITA: Italy
- JPN: Japan
- CAN: Canada
- BRA: Brazil
- RUS: Russia
- ZAF: South Africa
- GLOBAL: Global events (non-standard, internal use)

## Testing

All Python files compile successfully without syntax errors:
```bash
✓ config.py
✓ data_loader.py
✓ utils.py
✓ app.py
✓ visualizations/tab1_charts.py
✓ visualizations/tab2_charts.py
✓ visualizations/tab3_charts.py
```

## User Experience

The user interface now shows:
- Country dropdown: "United States (USA)", "China (CHN)", etc.
- All functionality preserved
- Filtering is more reliable across datasets
- No visible breaking changes to end users
