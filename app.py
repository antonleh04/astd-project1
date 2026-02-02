import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(
    page_title="ALLSTAT CO2 Dashboard",
    page_icon="🌍",
    layout="wide"
)

# 2. Header and Project Context
st.title("🌍 CO2 Emissions Visualization Prototype")
st.markdown("""
    *Developed for ALLSTAT - Official Statistics Data Exploration*
    ---
""")

# 3. Data Loading (Requirement 1.1)
@st.cache_data
def load_data():
    # Placeholder for your CO2.xlsx file
    # df = pd.read_excel("CO2.xlsx")
    # return df
    pass

# 4. Sidebar - Navigation & Filters (Requirement 1.3: Dynamicity)
with st.sidebar:
    st.header("Dashboard Controls")
    st.info("Use these filters to explore the spatio-temporal data.")
    # Example filters
    year_range = st.slider("Select Year Range", 1990, 2026, (2000, 2026))
    region_filter = st.multiselect("Select Regions", ["Global", "North America", "Europe", "Asia"])

# 5. Main Dashboard Layout (Requirement 2.1)
# Top Row: Key Metrics (Requirement: Statistics/Summarization)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Emissions", "1.2B Tons", "+5%")
with col2:
    st.metric("Avg. Per Capita", "4.5 Tons", "-2%")
with col3:
    st.metric("Top Contributor", "Sector A")

st.write("---")

# Middle Row: Spatio-Temporal Graphics (Requirement 1.2 & 2.1)
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📈 Time Series Trends")
    st.caption("Temporal analysis of CO2 fluctuations.")
    # PLACEHOLDER: px.line chart
    st.info("Insert Time Series Chart here.")

with col_right:
    st.subheader("🗺️ Geographic Distribution")
    st.caption("Spatial mapping of emission hotspots.")
    # PLACEHOLDER: px.choropleth (Non-basic graphic)
    st.info("Insert Map Graphic here.")

# Bottom Row: Complex/Non-Basic Visuals (Requirement 1.3)
st.subheader("🔬 Advanced Correlation Analysis")
# PLACEHOLDER: Heatmap, Box-plots, or Interactive Scatter
st.info("Insert Non-basic graphic (e.g., Correlation Heatmap or Treemap) here.")

# 6. Conclusion Section (Requirement 3.1)
with st.expander("View Analysis Summary"):
    st.write("""
        Based on the visualizations above, the prototype demonstrates... 
        (Add your project conclusions here).
    """)

# Footer
st.markdown("---")
st.caption("Group Project - Submission Date: Feb 08, 2026")