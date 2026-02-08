# Project 1 - CO2 Emissions Analysis Dashboard

This project is a Streamlit application for analyzing CO2 emissions data.

## Project Structure

**Quick overview:**
- `app.py` - Main Streamlit application (entry point, ~250 lines)
- `config.py` - Configuration, constants, and color palettes
- `data_loader.py` - Data loading and preprocessing functions
- `utils.py` - Utility functions (event filtering, annotations)
- `visualizations/` - Chart rendering modules organized by dashboard tab
  - `tab1_charts.py` - The Big Picture visualizations
  - `tab2_charts.py` - Equity & Economy visualizations
  - `tab3_charts.py` - Sectoral Deep Dive visualizations
- `app_old.py` - Backup of the original monolithic file

## Setup

1.  **Create and Activate Conda Environment:**
    ```bash
    conda env create -f environment.yml
    conda activate astd-project1
    ```


2. **Run the streamlit application**

```bash
streamlit run app.py
```

