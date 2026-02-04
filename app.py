import streamlit as st
import pandas as pd
import plotly.express as px

# --- Config ---
st.set_page_config(page_title="ALLSTAT CO2 Prototype", layout="wide")

# Custom CSS for aesthetics
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_events_data(file_path):
    df_events = pd.read_csv(file_path)
    df_events['Year'] = pd.to_numeric(df_events['Year'], errors='coerce')
    df_events.dropna(subset=['Year'], inplace=True)
    df_events['Year'] = df_events['Year'].astype(int)
    return df_events

@st.cache_data
def load_data(file_path):
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
    
    for df in [df_totals, df_capita, df_sector]:
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df.dropna(subset=['Year'], inplace=True)
        df['Year'] = df['Year'].astype(int)
        
    return df_totals, df_capita, df_sector

def add_events_to_fig(fig, events, selected_countries, year_range):
    events_in_range = events[
        (events['Year'].between(*year_range)) & 
        (events['Country'].isin(selected_countries + ['Global']))
    ]
    for _, event in events_in_range.iterrows():
        fig.add_vline(
            x=event['Year'], 
            line_width=1, 
            line_dash="dash", 
            line_color="grey",
            annotation_text=event['Event'],
            annotation_position="top left",
            annotation_font_size=10,
            annotation_hovertext=f"<b>{event['Event']} ({event['Year']})</b><br>{event['Description']}"
        )

# Load data
try:
    df_totals, df_capita, df_sector = load_data("datasets/CO2.xlsx")
    df_events = load_events_data("datasets/Top_20_GDP_CO2_Events_1970_2022.csv")
except FileNotFoundError:
    st.error("Data file not found. Please ensure the datasets directory contains 'CO2.xlsx' and the events CSV.")
    st.stop()

# --- Sidebar Filters ---
with st.sidebar:
    st.title("Project 1")
    st.info("**Legend & Info:** Visualizing CO2 datasets with imputed and scaled values.")
    
    st.header("Global Filters")
    min_y, max_y = int(df_totals['Year'].min()), int(df_totals['Year'].max())
    year_range = st.slider("Time Range", min_y, max_y, (1970, max_y))

    st.divider()

    show_events = st.checkbox("Show Historic Events", value=False)

    st.divider()
    
    available_countries = sorted(df_totals['Country'].unique())
    all_countries_selected = st.checkbox("Select All Countries", value=False)
    
    if all_countries_selected:
        selected_countries = available_countries
        st.info(f"Including all {len(available_countries)} countries/regions.")
    else:
        defaults = [c for c in ["USA", "China", "India"] if c in available_countries]
        selected_countries = st.multiselect("Select Specific Countries", available_countries, default=defaults)

if not selected_countries:
    st.warning("Please select at least one country to view the dashboard.")
    st.stop()

# --- Filtering Logic ---
mask_totals = (df_totals['Country'].isin(selected_countries)) & (df_totals['Year'].between(*year_range))
df_t_filtered = df_totals[mask_totals]
latest_year = df_t_filtered['Year'].max()

mask_capita = (df_capita['Country'].isin(selected_countries)) & (df_capita['Year'].between(*year_range))
df_c_filtered = df_capita[mask_capita]

mask_sector = (df_sector['Country'].isin(selected_countries)) & (df_sector['Year'].between(*year_range))
df_s_filtered = df_sector[mask_sector]

# --- Dashboard UI ---
st.title("CO2 Emissions Analysis Dashboard")
tab1, tab2, tab3 = st.tabs(["CO2 Total", "CO2 per Capita", "CO2 per Sector"])

# --- Tab 1: Total Emissions ---
with tab1:
    # Top Row: Metrics
    m1, m2, m3 = st.columns(3)
    avg_emissions = df_t_filtered['CO2'].mean()
    variance = df_t_filtered['CO2'].var() if len(df_t_filtered) > 1 else 0
    m1.metric("Avg Emission", f"{avg_emissions:,.2f} Mt")
    m2.metric("Variance", f"{variance:,.2e}")
    m3.metric("Selected Countries", len(selected_countries))

    # Graph Row 1: Treemap
    st.subheader(f"Emissions Treemap ({latest_year})")
    if not df_t_filtered.empty:
        fig_tree = px.treemap(df_t_filtered[df_t_filtered['Year'] == latest_year], 
                             path=['Country'], values='CO2',
                             color='CO2', color_continuous_scale='Reds')
        st.plotly_chart(fig_tree, use_container_width=True)

    # Graph Row 2: Trend
    st.subheader("Emissions Trend Over Time")
    fig_line = px.line(df_t_filtered, x='Year', y='CO2', color='Country', markers=len(selected_countries) < 10)
    if show_events:
        add_events_to_fig(fig_line, df_events, selected_countries, year_range)
    st.plotly_chart(fig_line, use_container_width=True)


# --- Tab 2: Per Capita ---
with tab2:
    # Graph Row 1: Heatmap
    st.subheader("Emissions per Capita Heatmap")
    if not df_c_filtered.empty:
        pivot_capita = df_c_filtered.pivot(index='Country', columns='Year', values='CO2_per_capita')
        fig_heat = px.imshow(pivot_capita, color_continuous_scale='Viridis', aspect="auto")
        st.plotly_chart(fig_heat, use_container_width=True)
    

    # Graph Row 2: Race Chart
    st.subheader("Top 10 Race: Emitters Per Capita Over Time")
    df_race = df_c_filtered.sort_values(['Year', 'CO2_per_capita'], ascending=[True, False])
    df_race = df_race.groupby('Year').head(10).reset_index(drop=True)

    if not df_race.empty:
        x_limit = df_race['CO2_per_capita'].max() * 1.1
        fig_race = px.bar(df_race, x="CO2_per_capita", y="Country", color="Country",
                          animation_frame="Year", animation_group="Country", orientation='h',
                          range_x=[0, x_limit], labels={'CO2_per_capita': 'Tonnes/Capita'})
        fig_race.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500, showlegend=False)
        fig_race.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 600 
        st.plotly_chart(fig_race, use_container_width=True)

# --- Tab 3: Sector Analysis ---
with tab3:
    # Graph Row 1: Sector Treemap
    st.subheader(f"Regional Sector Breakdown ({latest_year})")
    if not df_s_filtered.empty:
        fig_sec_tree = px.treemap(df_s_filtered[df_s_filtered['Year'] == latest_year], 
                                  path=['Country', 'Sector'], values='CO2', color='Sector')
        st.plotly_chart(fig_sec_tree, use_container_width=True)

    # Graph Row 2: Sector Composition Over Time
    st.subheader("Sector Composition Over Time")
    if not df_s_filtered.empty:
        sector_agg = df_s_filtered.groupby(['Year', 'Sector'])['CO2'].sum().reset_index()
        fig_area = px.area(sector_agg, x="Year", y="CO2", color="Sector")
        st.plotly_chart(fig_area, use_container_width=True)

    st.divider()

    # Section 3: Deep Dive
    st.subheader("Sector specific Analysis")
    if not df_s_filtered.empty:
        sector_list = sorted(df_s_filtered['Sector'].unique())
        selected_sector = st.selectbox("Pick a Sector to analyze:", sector_list)
        
        sector_specific_df = df_s_filtered[
            (df_s_filtered['Sector'] == selected_sector) & (df_s_filtered['Year'] == latest_year)
        ]
        
        total_sector_co2 = sector_specific_df['CO2'].sum()
        st.metric(f"Total {selected_sector} Emissions", f"{total_sector_co2:,.2f} Mt")
        
        # Graph Row 4: Drill-down Bar Chart
        fig_dom = px.bar(sector_specific_df.sort_values('CO2', ascending=False),
                        x='CO2', y='Country', orientation='h', color='CO2',
                        color_continuous_scale='Viridis', title=f"Country Ranking in {selected_sector}")
        st.plotly_chart(fig_dom, use_container_width=True)