import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

#region config
st.set_page_config(page_title="ALLSTAT CO2 Prototype", layout="wide")

# Custom CSS for aesthetics
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .main { background-color: #f5f7f9; }
    </style>
    """, unsafe_allow_html=True)

#region data
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

@st.cache_data
def load_land_area_data(file_path):
    df_land_area = pd.read_csv(file_path, skiprows=4)
    df_land_area = df_land_area.melt(
        id_vars=['Country Name', 'Country Code', 'Indicator Name', 'Indicator Code'],
        var_name='Year',
        value_name='Land area (sq. km)'
    )
    df_land_area['Year'] = pd.to_numeric(df_land_area['Year'], errors='coerce')
    df_land_area.dropna(subset=['Year'], inplace=True)
    df_land_area['Year'] = df_land_area['Year'].astype(int)
    df_land_area.rename(columns={'Country Name': 'Country'}, inplace=True)
    df_land_area['Land area (sq. km)'] = pd.to_numeric(df_land_area['Land area (sq. km)'], errors='coerce')
    return df_land_area

@st.cache_data
def load_gdp_data(file_path):
    df_gdp = pd.read_csv(file_path, skiprows=4)
    df_gdp = df_gdp.melt(
        id_vars=['Country Name', 'Country Code', 'Indicator Name', 'Indicator Code'],
        var_name='Year',
        value_name='GDP Growth (annual %)'
    )
    df_gdp['Year'] = pd.to_numeric(df_gdp['Year'], errors='coerce')
    df_gdp.dropna(subset=['Year'], inplace=True)
    df_gdp['Year'] = df_gdp['Year'].astype(int)
    df_gdp.rename(columns={'Country Name': 'Country'}, inplace=True)
    df_gdp['GDP Growth (annual %)'] = pd.to_numeric(df_gdp['GDP Growth (annual %)'], errors='coerce')
    return df_gdp

# Load data
try:
    df_totals, df_capita, df_sector = load_data("datasets/CO2.xlsx")
    df_events = load_events_data("datasets/Top_20_GDP_CO2_Events_1970_2022.csv")
    df_land_area = load_land_area_data("datasets/land_area_data/API_AG.LND.TOTL.K2_DS2_en_csv_v2_323.csv")
    df_gdp_growth = load_gdp_data("datasets/gdp_data/API_NY.GDP.MKTP.KD.ZG_DS2_en_csv_v2_40824.csv")
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

#region filter data
mask_totals = (df_totals['Country'].isin(selected_countries)) & (df_totals['Year'].between(*year_range))
df_t_filtered = df_totals[mask_totals]
latest_year = df_t_filtered['Year'].max()

mask_capita = (df_capita['Country'].isin(selected_countries)) & (df_capita['Year'].between(*year_range))
df_c_filtered = df_capita[mask_capita]

mask_sector = (df_sector['Country'].isin(selected_countries)) & (df_sector['Year'].between(*year_range))
df_s_filtered = df_sector[mask_sector]

# --- Dashboard UI ---
st.title("CO2 Emissions Analysis Dashboard")
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["CO2 Total", "CO2 per Capita", "CO2 per Sector", "GDP vs CO2", "Development Trajectories", "Sectoral Fingerprint"])

# region total emmisions
with tab1:
    # Top Row: Metrics
    m1, m2, m3 = st.columns(3)
    avg_emissions = df_t_filtered['CO2'].mean()
    variance = df_t_filtered['CO2'].var() if len(df_t_filtered) > 1 else 0
    m1.metric("Avg Emission", f"{avg_emissions:,.2f} Mt")
    m2.metric("Variance", f"{variance:,.2e}")
    m3.metric("Selected Countries", len(selected_countries))

    # Graph Row 1: Treemap (sized by Land Area, colored by CO2)
    st.subheader(f"Emissions Treemap by Land Area ({latest_year})")
    if not df_t_filtered.empty:
        # Filter land area data for the latest year and selected countries
        df_land_area_latest = df_land_area[
            (df_land_area['Year'] == latest_year) & 
            (df_land_area['Country'].isin(selected_countries))
        ]
        
        # Merge CO2 data with land area data
        df_merged_for_treemap = pd.merge(
            df_t_filtered[df_t_filtered['Year'] == latest_year],
            df_land_area_latest[['Country', 'Land area (sq. km)']],
            on='Country',
            how='left'
        )
        
        
        # Drop rows where 'Land area (sq. km)' is NaN after merge
        df_merged_for_treemap.dropna(subset=['Land area (sq. km)'], inplace=True)
        
        if df_merged_for_treemap.empty:
            st.warning("No land area data available for the selected countries and year to display the treemap.")
        else:
            fig_tree = px.treemap(df_merged_for_treemap, 
                                 path=['Country'], values='Land area (sq. km)',
                                 color='CO2', color_continuous_scale='Reds',
                                 hover_data={'CO2': ':.2f'})
            st.plotly_chart(fig_tree, use_container_width=True)

    # Graph Row 2: Trend
    st.subheader("Emissions Trend Over Time")
    fig_line = px.line(df_t_filtered, x='Year', y='CO2', color='Country', markers=len(selected_countries) < 10)
    if show_events:
        add_events_to_fig(fig_line, df_events, selected_countries, year_range)
    st.plotly_chart(fig_line, use_container_width=True)


# region per capita
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

# region sector analysis
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

# region gdp vs co2
with tab4:
    st.subheader("CO2 Emissions vs. GDP Growth (Annual %)")
    
    # Allow user to select a single year for this plot
    min_gdp_year = max(df_t_filtered['Year'].min(), df_gdp_growth['Year'].min())
    max_gdp_year = min(df_t_filtered['Year'].max(), df_gdp_growth['Year'].max())
    
    if min_gdp_year > max_gdp_year:
        st.warning("No overlapping years for CO2 emissions and GDP growth data with current filters.")
        st.stop()
        
    gdp_year = st.slider("Select Year for GDP vs CO2 Plot", 
                         min_gdp_year, max_gdp_year, max_gdp_year)
    
    st.subheader(f"CO2 Emissions vs. GDP Growth (Annual %) in {gdp_year}")

    # Filter CO2 and GDP data for the selected year and countries
    df_t_gdp_year = df_totals[
        (df_totals['Country'].isin(selected_countries)) &
        (df_totals['Year'] == gdp_year)
    ]
    df_gdp_gdp_year = df_gdp_growth[
        (df_gdp_growth['Country'].isin(selected_countries)) &
        (df_gdp_growth['Year'] == gdp_year)
    ]
    
    # Merge CO2 totals with GDP growth data for the selected year
    df_merged_gdp_co2 = pd.merge(
        df_t_gdp_year,
        df_gdp_gdp_year,
        on=['Country', 'Year'],
        how='inner'  # Use inner merge to only keep rows with both CO2 and GDP data
    )
    
    # Drop rows with NaN values in either CO2 or GDP Growth (annual %)
    df_merged_gdp_co2.dropna(subset=['CO2', 'GDP Growth (annual %)'], inplace=True)
    
    if df_merged_gdp_co2.empty:
        st.warning(f"No combined CO2 and GDP growth data available for the selected countries in {gdp_year}.")
    else:
        fig_gdp_co2 = px.scatter(df_merged_gdp_co2, 
                                 x='CO2', 
                                 y='GDP Growth (annual %)', 
                                 color='Country',
                                 hover_name='Country',
                                 hover_data={'Year': True, 
                                               'CO2': ':.2f', 
                                               'GDP Growth (annual %)': ':.2f'}
                                )
        fig_gdp_co2.update_layout(xaxis_title="CO2 Emissions (Mt)",
                                 yaxis_title="GDP Growth (Annual %)")
        st.plotly_chart(fig_gdp_co2, use_container_width=True)

# region development trajectories
with tab5:
    st.subheader("CO2 Development Trajectories")
    st.markdown("**Connected scatter plot showing how countries evolved from per capita to total emissions over time.**")
    
    # Merge total emissions and per capita data
    df_trajectory = pd.merge(
        df_t_filtered[['Country', 'Year', 'CO2']],
        df_c_filtered[['Country', 'Year', 'CO2_per_capita']],
        on=['Country', 'Year'],
        how='inner'
    )
    
    if df_trajectory.empty:
        st.warning("No trajectory data available for the selected countries and time range.")
    else:
        # Create connected scatter plot
        fig_trajectory = px.line(
            df_trajectory.sort_values(['Country', 'Year']),
            x='CO2_per_capita',
            y='CO2',
            color='Country',
            markers=True,
            hover_data={
                'Country': True,
                'Year': True,
                'CO2': ':.2f',
                'CO2_per_capita': ':.2f'
            },
            labels={
                'CO2_per_capita': 'Per Capita Emissions (t CO2/cap/yr)',
                'CO2': 'Total Emissions (Mt CO2/yr)'
            }
        )
        
        # Styling
        fig_trajectory.update_layout(
            template='plotly_white',
            yaxis_range=[0, df_trajectory['CO2'].max() * 1.1],
            hovermode='closest'
        )
        
        st.plotly_chart(fig_trajectory, use_container_width=True)
        
        # Add explanation
        st.info("💡 **How to read this chart:** Each line represents a country's trajectory over time. " +
                "Movement to the right indicates increasing per capita emissions, while upward movement " +
                "shows increasing total emissions. The markers represent individual years.")

# region sectoral fingerprint
with tab6:
    st.subheader("Sectoral Emission Fingerprint")
    st.markdown("**Compare the emission profiles of two countries across different sectors.**")
    
    # Get available years from sector data
    min_sector_year = int(df_sector['Year'].min())
    max_sector_year = int(df_sector['Year'].max())
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        radar_year = st.slider("Select Year for Comparison", 
                               min_sector_year, max_sector_year, max_sector_year,
                               key="radar_year")
    
    with col2:
        show_percentage = st.radio("Display Mode", 
                                   ["Absolute Values (Mt CO2)", "Relative Percentage (%)"],
                                   index=1)
    
    st.divider()
    
    # Use the globally selected countries from sidebar
    if len(selected_countries) == 0:
        st.warning("Please select at least 1 country in the sidebar to view sectoral profile.")
        st.stop()
    
    # Display which countries are being compared
    if len(selected_countries) == 1:
        st.info(f"📊 **Viewing:** {selected_countries[0]}")
    else:
        st.info(f"📊 **Comparing {len(selected_countries)} countries:** {', '.join(selected_countries)}")
    
    # Filter sector data for selected year and all selected countries
    df_radar = df_sector[
        (df_sector['Year'] == radar_year) & 
        (df_sector['Country'].isin(selected_countries))
    ]
    
    if df_radar.empty:
        st.warning(f"No sector data available for the selected country/countries in {radar_year}.")
    else:
        # Group by country and sector
        df_radar_grouped = df_radar.groupby(['Country', 'Sector'])['CO2'].sum().reset_index()
        
        # Calculate percentages if needed
        if "Percentage" in show_percentage:
            # Calculate total emissions per country
            country_totals = df_radar_grouped.groupby('Country')['CO2'].sum().to_dict()
            df_radar_grouped['Value'] = df_radar_grouped.apply(
                lambda row: (row['CO2'] / country_totals[row['Country']]) * 100, axis=1
            )
            value_label = "Percentage (%)"
        else:
            df_radar_grouped['Value'] = df_radar_grouped['CO2']
            value_label = "Emissions (Mt CO2)"
        
        # Get all sectors
        all_sectors = sorted(df_radar_grouped['Sector'].unique())
        
        # Create radar chart
        fig_radar = go.Figure()
        
        # Add trace for each selected country
        max_value = 0
        for country in selected_countries:
            df_country = df_radar_grouped[df_radar_grouped['Country'] == country]
            if not df_country.empty:
                values = [df_country[df_country['Sector'] == sector]['Value'].iloc[0] 
                         if not df_country[df_country['Sector'] == sector].empty else 0 
                         for sector in all_sectors]
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=values,
                    theta=all_sectors,
                    fill='toself',
                    name=country
                ))
                
                max_value = max(max_value, max(values) if values else 0)
        
        # Create title based on number of countries
        if len(selected_countries) == 1:
            title_text = f"Sectoral Profile: {selected_countries[0]} ({radar_year})"
        else:
            title_text = f"Sectoral Comparison: {len(selected_countries)} Countries ({radar_year})"
        
        # Update layout
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max_value * 1.1]
                )
            ),
            showlegend=True,
            title=title_text,
            height=600
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
        
        # Add insights
        if len(selected_countries) == 1:
            comparison_text = "The shape reveals the sectoral structure of emissions."
        else:
            comparison_text = "Compare the shapes to see structural differences in sectoral profiles across countries."
        st.info(f"💡 **How to read this chart:** Each axis represents a sector. The distance from the center shows the emission level. {comparison_text}")