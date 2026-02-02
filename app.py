import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. PAGE CONFIG & STYLING
# ==========================================
st.set_page_config(page_title="ALLSTAT CO2 Prototype", layout="wide")

# Custom CSS to make containers look uniform
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADING (Cached for performance)
# ==========================================
@st.cache_data
def load_data(file_path):
    """Loads and reshapes Excel sheets into Long Format for Plotly."""
    xlsx = pd.ExcelFile(file_path)
    
    # Process Total Emissions
    df_totals = xlsx.parse('fossil_CO2_totals_by_country').melt(
        id_vars=['ISOcode', 'Country'], var_name='Year', value_name='CO2'
    )
    
    # Process Per Capita
    df_capita = xlsx.parse('fossil_CO2_per_capita_by_countr').melt(
        id_vars=['ISOcode', 'Country'], var_name='Year', value_name='CO2_per_capita'
    )
    
    # Process Sector Data
    df_sector = xlsx.parse('fossil_CO2_by_sector_and_countr').melt(
        id_vars=['Sector', 'ISOcode', 'Country'], var_name='Year', value_name='CO2'
    )
    
    # Clean Year column and handle missing values
    for df in [df_totals, df_capita, df_sector]:
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df.dropna(subset=['Year'], inplace=True)
        df['Year'] = df['Year'].astype(int)
        
    return df_totals, df_capita, df_sector

# Load the data
try:
    df_totals, df_capita, df_sector = load_data("datasets/CO2.xlsx")
except FileNotFoundError:
    st.error("Data file not found. Please ensure 'datasets/CO2.xlsx' exists.")
    st.stop()

# ==========================================
# 3. SIDEBAR FILTERS
# ==========================================
with st.sidebar:
    st.title("Project 1")
    st.info("**Legend & Info:** Visualizing CO2 datasets with imputed and scaled values.")
    
    st.header("Global Filters")
    
    # Country Selection
    available_countries = sorted(df_totals['Country'].unique())
    selected_countries = st.multiselect(
        "Select Countries", 
        available_countries, 
        default=["USA", "China", "India"] if "USA" in available_countries else available_countries[:3]
    )
    
    # Year Selection
    min_y, max_y = int(df_totals['Year'].min()), int(df_totals['Year'].max())
    year_range = st.slider("Time Range", min_y, max_y, (1990, max_y))

# ==========================================
# 4. FILTERING LOGIC
# ==========================================
# Apply filters to dataframes
mask_totals = (df_totals['Country'].isin(selected_countries)) & (df_totals['Year'].between(*year_range))
df_t_filtered = df_totals[mask_totals]

mask_capita = (df_capita['Country'].isin(selected_countries)) & (df_capita['Year'].between(*year_range))
df_c_filtered = df_capita[mask_capita]

mask_sector = (df_sector['Country'].isin(selected_countries)) & (df_sector['Year'].between(*year_range))
df_s_filtered = df_sector[mask_sector]

# ==========================================
# 5. MAIN DASHBOARD UI
# ==========================================
st.title("CO2 Emissions Analysis Dashboard")

tab1, tab2, tab3 = st.tabs(["CO2 Total", "CO2 per Capita", "CO2 per Sector"])

# --- TAB 1: TOTAL EMISSIONS ---
with tab1:
    # Metrics
    m1, m2, m3 = st.columns(3)
    avg_emissions = df_t_filtered['CO2'].mean()
    variance = df_t_filtered['CO2'].var()
    
    m1.metric("Avg Emission", f"{avg_emissions:,.2f} Mt")
    m2.metric("Variance", f"{variance:,.2e}")
    m3.metric("Selected Countries", len(selected_countries))

    # Visuals Row 1
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Emissions Treemap (Recent Year)")
        latest_year = df_t_filtered['Year'].max()
        fig_tree = px.treemap(df_t_filtered[df_t_filtered['Year'] == latest_year], 
                             path=['Country'], values='CO2',
                             color='CO2', color_continuous_scale='Reds')
        st.plotly_chart(fig_tree, use_container_width=True)
        
    with col2:
        st.subheader("Emissions Trend")
        fig_line = px.line(df_t_filtered, x='Year', y='CO2', color='Country', markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

    # Historic Events (Placeholder for Event Analysis)
    st.subheader("Change Point Detection & Historic Events")
    fig_event = px.area(df_t_filtered, x='Year', y='CO2', color='Country', title="Cumulative Growth")
    st.plotly_chart(fig_event, use_container_width=True)

# --- TAB 2: PER CAPITA ---
with tab2:
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Emissions per Capita Heatmap")
        # Pivot for heatmap
        pivot_capita = df_c_filtered.pivot(index='Country', columns='Year', values='CO2_per_capita')
        fig_heat = px.imshow(pivot_capita, color_continuous_scale='Viridis', aspect="auto")
        st.plotly_chart(fig_heat, use_container_width=True)
        
    with col_b:
        st.subheader("Top Emitters (Per Capita)")
        top_10 = df_c_filtered[df_c_filtered['Year'] == latest_year].nlargest(10, 'CO2_per_capita')
        fig_bar = px.bar(top_10, x='CO2_per_capita', y='Country', orientation='h', color='Country')
        st.plotly_chart(fig_bar, use_container_width=True)

# --- TAB 3: SECTORS ---
with tab3:
    col_x, col_y = st.columns(2)
    with col_x:
        st.subheader("Sector Treemap")
        fig_sec_tree = px.treemap(df_s_filtered[df_s_filtered['Year'] == latest_year], 
                                 path=['Country', 'Sector'], values='CO2')
        st.plotly_chart(fig_sec_tree, use_container_width=True)
        
    with col_y:
        st.subheader("Sector Composition (Stacked Area)")
        # Summing sectors across selected countries
        sector_agg = df_s_filtered.groupby(['Year', 'Sector'])['CO2'].sum().reset_index()
        fig_area = px.area(sector_agg, x="Year", y="CO2", color="Sector")
        st.plotly_chart(fig_area, use_container_width=True)