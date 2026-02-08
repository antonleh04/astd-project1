"""
Tab 3 Charts: Sectoral Deep Dive
=================================
Visualizations for sector composition and fingerprints.
"""

import math
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import CLIMATE_QUALITATIVE, PLOTLY_TEMPLATE
from utils import add_events_to_fig


def render_tab3_charts(
    df_s_filtered: pd.DataFrame,
    df_events: pd.DataFrame,
    selected_iso_codes: list[str],
    year_range: tuple[int, int],
    latest_year: int,
    show_events: bool,
    evt_iso_codes: list[str],
):
    """Render all charts for Tab 3 (Sectoral Deep Dive)."""

    # ── Stacked area: sector composition for selected countries ──────────────
    st.subheader("Sector Composition Over Time")
    
    # Toggle for chart mode
    chart_mode = st.radio(
        "Chart Mode",
        ["Normalized (100%)", "Absolute Growth"],
        horizontal=True,
        label_visibility="collapsed",
    )
    is_normalized = chart_mode == "Normalized (100%)"

    if not selected_iso_codes:
        st.info("Please select at least one country.")
        return

    # Determine grid dimensions
    n_charts = len(selected_iso_codes)
    cols = 3
    rows = math.ceil(n_charts / cols)
    
    # Dynamic styling calculations
    row_height = 300
    vertical_gap_px = 50
    total_height = row_height * rows + 100  # +100 for legend/margin
    
    # Calculate vertical spacing as fraction of plot area
    # Guard against rows=1 where spacing doesn't matter but division by zero could occur if logic changes
    vertical_spacing = (vertical_gap_px / (row_height * rows)) if rows > 1 else 0.1

    # Create the subplot grid
    fig = make_subplots(
        rows=rows, 
        cols=cols, 
        subplot_titles=[
            df_s_filtered[df_s_filtered["ISOcode"] == iso]["Country"].iloc[0] 
            if not df_s_filtered[df_s_filtered["ISOcode"] == iso].empty else iso 
            for iso in selected_iso_codes
        ],
        vertical_spacing=vertical_spacing,
        horizontal_spacing=0.05,
        shared_xaxes=True,
        shared_yaxes=is_normalized, # Share Y-axis only if normalized (0-100%)
    )

    # Get unique sectors from the entire filtered dataset for consistent coloring
    all_sectors = sorted(df_s_filtered["Sector"].unique())
    # Create a mapping of sector to color
    sector_colors = {
        sec: CLIMATE_QUALITATIVE[i % len(CLIMATE_QUALITATIVE)] 
        for i, sec in enumerate(all_sectors)
    }

    # Track which sectors we've added to the legend to avoid duplicates
    sectors_in_legend = set()

    for i, iso in enumerate(selected_iso_codes):
        row = (i // cols) + 1
        col = (i % cols) + 1
        
        df_country = df_s_filtered[df_s_filtered["ISOcode"] == iso]
        
        if df_country.empty:
            continue
            
        # Group by Year and Sector to get totals
        sector_ts = df_country.groupby(["Year", "Sector"])["CO2"].sum().reset_index()
        
        # ── Densify data: Ensure all sectors exist for all years ─────────────────
        # This prevents stacking artifacts if a sector is missing in some years
        unique_years = sector_ts["Year"].unique()
        
        # Create a MultiIndex of all possible (Year, Sector) pairs
        full_idx = pd.MultiIndex.from_product(
            [unique_years, all_sectors], 
            names=["Year", "Sector"]
        )
        
        # Reindex and fill missing CO2 with 0
        sector_ts = (
            sector_ts.set_index(["Year", "Sector"])
            .reindex(full_idx, fill_value=0)
            .reset_index()
        )
        
        if is_normalized:
            # Calculate yearly totals to normalize
            yearly_totals = sector_ts.groupby("Year")["CO2"].transform("sum")
            
            # Avoid division by zero
            sector_ts["Value"] = sector_ts.apply(
                lambda x: (x["CO2"] / yearly_totals[x.name] * 100) if yearly_totals[x.name] > 0 else 0, 
                axis=1
            )
            y_hover_fmt = ".1f"
            y_hover_suffix = "%"
        else:
            # Use absolute values
            sector_ts["Value"] = sector_ts["CO2"]
            y_hover_fmt = ",.2f"
            y_hover_suffix = " Mt"
        
        # Sort to ensure proper stacking order
        for sec in all_sectors:
            df_sec = sector_ts[sector_ts["Sector"] == sec].sort_values("Year")
            
            show_legend = sec not in sectors_in_legend
            if show_legend:
                sectors_in_legend.add(sec)
            
            fig.add_trace(
                go.Scatter(
                    x=df_sec["Year"], 
                    y=df_sec["Value"],
                    mode="lines", 
                    name=sec, 
                    stackgroup="one",
                    line=dict(width=0.5, color=sector_colors[sec]),
                    fillcolor=sector_colors[sec],
                    opacity=1,
                    showlegend=show_legend,
                    hovertemplate=(
                        f"<b>{sec}</b><br>"
                        "Year: %{x}<br>"
                        f"Value: %{{y:{y_hover_fmt}}}{y_hover_suffix}<br>"
                        "CO2: %{customdata:,.2f} Mt<extra></extra>"
                    ),
                    customdata=df_sec["CO2"] # Pass absolute values for hover
                ),
                row=row, 
                col=col
            )

    # Update layout
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=total_height, # Use calculated total height
        hovermode="x unified",
        legend=dict(
            orientation="h", 
            yanchor="top", y=-0.1 / (rows * 0.3) if rows > 3 else -0.15, # Adjust legend position slightly based on rows
            xanchor="center", x=0.5
        ),
        margin=dict(l=50, r=30, t=60, b=100),
    )
    
    # Update y-axes
    y_title = "Share of Emissions (%)" if is_normalized else "CO2 Emissions (Mt)"
    y_range = [0, 100] if is_normalized else None
    
    fig.update_yaxes(title=y_title if cols == 1 else None, range=y_range)
    
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Sectoral Fingerprint Treemap ─────────────────────────────────────────
    st.subheader(f"Sectoral Fingerprint ({latest_year})")
    # st.markdown("##### Sector Breakdown Treemap")
    if not df_s_filtered.empty:
        df_sec_tree = df_s_filtered[df_s_filtered["Year"] == latest_year]
        if not df_sec_tree.empty:
            fig_sec_tm = px.treemap(
                df_sec_tree,
                path=["Country", "Sector"],
                values="CO2",
                color="Sector",
                color_discrete_sequence=CLIMATE_QUALITATIVE,
            )
            fig_sec_tm.update_layout(
                template=PLOTLY_TEMPLATE,
                height=500,
                margin=dict(l=10, r=10, t=30, b=10),
            )
            st.plotly_chart(fig_sec_tm, use_container_width=True)
        else:
            st.info("No sector data for the latest year.")
    else:
        st.info("No sector data available.")
