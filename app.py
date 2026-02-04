import streamlit as st
import pandas as pd
import plotly.express as px

#config
st.set_page_config(page_title="ALLSTAT CO2 Prototype", layout="wide")

# Custom CSS to make containers look uniform
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)


#region load data

@st.cache_data
def load_events_data(file_path):
    """Loads historical events data."""
    df_events = pd.read_csv(file_path)
    df_events['Year'] = pd.to_numeric(df_events['Year'], errors='coerce')
    df_events.dropna(subset=['Year'], inplace=True)
    df_events['Year'] = df_events['Year'].astype(int)
    return df_events

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

def add_events_to_fig(fig, events, selected_countries, year_range):
    """Adds historical events to a plotly figure."""
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

# Load the data
try:
    df_totals, df_capita, df_sector = load_data("datasets/CO2.xlsx")
    df_events = load_events_data("datasets/Top_20_GDP_CO2_Events_1970_2022.csv")
except FileNotFoundError:
    st.error("Data file not found. Please ensure 'datasets/CO2.xlsx' exists.")
    st.stop()

#region sidebar filters
with st.sidebar:
    st.title("Project 1")
    st.info("**Legend & Info:** Visualizing CO2 datasets with imputed and scaled values.")
    
    st.header("Global Filters")
    
    # --- 1. Year Selection ---
    min_y, max_y = int(df_totals['Year'].min()), int(df_totals['Year'].max())
    year_range = st.slider("Time Range", min_y, max_y, (1990, max_y))

    # --- Historic Events Toggle ---
    show_events = st.checkbox("Show Historic Events", value=True)

    st.divider()

    # --- 2. Country Selection Logic ---
    available_countries = sorted(df_totals['Country'].unique())
    
    # "Select All" Checkbox
    all_countries_selected = st.checkbox("Select All Countries", value=False)
    
    if all_countries_selected:
        # If checked, use all countries and disable the specific selector
        selected_countries = available_countries
        st.info(f"Including all {len(available_countries)} countries/regions.")
        
        # Optional: Show disabled multiselect for visual confirmation
        st.multiselect(
            "Select specific countries (Disabled while 'Select All' is on)", 
            available_countries, 
            default=available_countries[:3], 
            disabled=True
        )
    else:
        # If unchecked, enable specific selection
        # Ensure defaults exist in data
        defaults = ["USA", "China", "India"]
        defaults = [c for c in defaults if c in available_countries]
        
        selected_countries = st.multiselect(
            "Select Specific Countries", 
            available_countries, 
            default=defaults
        )


if not selected_countries:
    st.warning("Please select at least one country or check 'Select All Countries' to view the dashboard.")
    st.stop()


#region data filtering

# Apply filters to dataframes
mask_totals = (df_totals['Country'].isin(selected_countries)) & (df_totals['Year'].between(*year_range))
df_t_filtered = df_totals[mask_totals]

mask_capita = (df_capita['Country'].isin(selected_countries)) & (df_capita['Year'].between(*year_range))
df_c_filtered = df_capita[mask_capita]

mask_sector = (df_sector['Country'].isin(selected_countries)) & (df_sector['Year'].between(*year_range))
df_s_filtered = df_sector[mask_sector]

#region dashboard
st.title("CO2 Emissions Analysis Dashboard")

tab1, tab2, tab3 = st.tabs(["CO2 Total", "CO2 per Capita", "CO2 per Sector"])

#region total emmisions
with tab1:
    # Metrics
    avg_emissions = df_t_filtered['CO2'].mean()
    
    # Handle variance calculation for single data point
    if len(df_t_filtered) > 1:
        variance = df_t_filtered['CO2'].var()
    else:
        variance = 0
    
    st.metric("Avg Emission", f"{avg_emissions:,.2f} Mt")
    st.metric("Variance", f"{variance:,.2e}")
    st.metric("Selected Countries", len(selected_countries))

    # Visuals Row 1
    st.subheader("Emissions Treemap (Recent Year)")
    if not df_t_filtered.empty:
        latest_year = df_t_filtered['Year'].max()
        fig_tree = px.treemap(df_t_filtered[df_t_filtered['Year'] == latest_year], 
                             path=['Country'], values='CO2',
                             color='CO2', color_continuous_scale='Reds')
        st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.info("No data for Treemap")
    
    st.subheader("Emissions Trend")
    fig_line = px.line(df_t_filtered, x='Year', y='CO2', color='Country', markers=len(selected_countries) < 10)
    
    if show_events:
        add_events_to_fig(fig_line, df_events, selected_countries, year_range)

    st.plotly_chart(fig_line, use_container_width=True)

    # Historic Events
    st.subheader("Cumulative Growth")
    fig_event = px.area(df_t_filtered, x='Year', y='CO2', color='Country')
    if show_events:
        add_events_to_fig(fig_event, df_events, selected_countries, year_range)
    st.plotly_chart(fig_event, use_container_width=True)

#region per capita
with tab2:
    if len(selected_countries) > 20 and not all_countries_selected:
        st.warning("Displaying Heatmap for many countries may look crowded.")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("Emissions per Capita Heatmap")
        if not df_c_filtered.empty:
            pivot_capita = df_c_filtered.pivot(index='Country', columns='Year', values='CO2_per_capita')
            fig_heat = px.imshow(pivot_capita, color_continuous_scale='Viridis', aspect="auto")
            st.plotly_chart(fig_heat, use_container_width=True)
        
    with col_b:
        st.subheader(f"Top 10 Emitters ({latest_year})")
        if not df_c_filtered.empty:
            top_10 = df_c_filtered[df_c_filtered['Year'] == latest_year].nlargest(10, 'CO2_per_capita')
            fig_bar = px.bar(top_10, x='CO2_per_capita', y='Country', orientation='h', color='Country')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider() 
    
    st.subheader("Top 10 Race: Emitters Per Capita")
    
    # Race Chart Logic
    df_race = df_c_filtered.sort_values(['Year', 'CO2_per_capita'], ascending=[True, False])
    # Filter to only top 10 per year to make animation smooth
    df_race = df_race.groupby('Year').head(10).reset_index(drop=True)

    if not df_race.empty:
        x_limit = df_race['CO2_per_capita'].max() * 1.1

        fig_race = px.bar(
            df_race,
            x="CO2_per_capita",
            y="Country",
            color="Country",
            animation_frame="Year",
            animation_group="Country",
            orientation='h',
            range_x=[0, x_limit],
            labels={'CO2_per_capita': 'Tonnes/Capita'}
        )

        fig_race.update_layout(
            yaxis={'categoryorder': 'total ascending'}, 
            margin=dict(t=20, l=0, r=0, b=0),
            height=500,
            showlegend=False
        )

        # Animation control speed
        fig_race.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 600 
        fig_race.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 300

        st.plotly_chart(fig_race, use_container_width=True)
    else:
        st.info("Not enough data for Race Chart")

#region sector analysis
with tab3:
    col_x, col_y = st.columns(2)
    
    with col_x:
        st.subheader("Regional Sector Breakdown")
        if not df_s_filtered.empty:
            # Treemap showing Country -> Sector
            fig_sec_tree = px.treemap(
                df_s_filtered[df_s_filtered['Year'] == latest_year], 
                path=['Country', 'Sector'], 
                values='CO2',
                color='Sector'
            )
            st.plotly_chart(fig_sec_tree, use_container_width=True)
        else:
            st.info("No Sector data available")

    with col_y:
        st.subheader("Sector Composition Over Time")
        if not df_s_filtered.empty:
            # Aggregated Area Chart
            sector_agg = df_s_filtered.groupby(['Year', 'Sector'])['CO2'].sum().reset_index()
            fig_area = px.area(sector_agg, x="Year", y="CO2", color="Sector")
            st.plotly_chart(fig_area, use_container_width=True)

    st.divider()

    # --- NEW: Sector-Specific Deep Dive ---
    st.subheader("Sector Drill-Down: Who dominates the industry?")
    
    if not df_s_filtered.empty:
        # 1. Create a selection list of sectors available in the data
        sector_list = sorted(df_s_filtered['Sector'].unique())
        selected_sector = st.selectbox("Pick a Sector to analyze:", sector_list)

        # 2. Filter data for just that sector and the latest year
        sector_specific_df = df_s_filtered[
            (df_s_filtered['Sector'] == selected_sector) & 
            (df_s_filtered['Year'] == latest_year)
        ]

        # 3. Visuals for the Drill-Down
        c1, c2 = st.columns([1, 2])
        
        with c1:
            # Metric for the sector
            total_sector_co2 = sector_specific_df['CO2'].sum()
            st.metric(f"Total {selected_sector} Emissions", f"{total_sector_co2:,.2f} Mt")
            st.caption(f"Based on selected countries for {latest_year}")

        with c2:
            # Bar chart showing which country is responsible for the most in this sector
            fig_dom = px.bar(
                sector_specific_df.sort_values('CO2', ascending=False),
                x='CO2',
                y='Country',
                orientation='h',
                color='CO2',
                color_continuous_scale='Viridis',
                title=f"Country Ranking in {selected_sector}"
            )
            st.plotly_chart(fig_dom, use_container_width=True)