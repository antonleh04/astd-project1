"""
Tab 1 Charts: The Big Picture
==============================
Visualizations for aggregate trends, KPIs, and treemaps.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from config import CLIMATE_QUALITATIVE, PLOTLY_TEMPLATE, CHART_MARGIN
from utils import add_events_to_fig


def render_tab1_charts(
    df_t_filtered: pd.DataFrame,
    df_c_filtered: pd.DataFrame,
    df_events: pd.DataFrame,
    selected_iso_codes: list[str],
    year_range: tuple[int, int],
    latest_year: int,
    show_events: bool,
    evt_iso_codes: list[str],
):
    """Render all charts for Tab 1 (The Big Picture)."""
    
    m1, m2, m3, m4 = st.columns(4)

    latest_total = df_t_filtered[df_t_filtered["Year"] == latest_year]["CO2"].sum()
    cumulative_total = df_t_filtered["CO2"].sum()

    start_year = df_t_filtered["Year"].min()
    start_total = df_t_filtered[df_t_filtered["Year"] == start_year]["CO2"].sum()
    
    if start_total > 0 and latest_year > start_year:
        years_diff = latest_year - start_year
        cagr = ((latest_total / start_total) ** (1 / years_diff)) - 1
    else:
        cagr = 0.0

    m1.metric("Latest Annual Total", f"{latest_total:,.0f} Mt")
    m2.metric(
        "Cumulative Total", 
        f"{cumulative_total / 1000:,.1f} Gt",
        help="Total emissions accumulated over the selected time range (Gigatonnes)."
    )
    m3.metric(
        "Trend (CAGR)", 
        f"{cagr * 100:+.2f}%",
        help=f"Compound Annual Growth Rate from {start_year} to {latest_year}."
    )
    m4.metric("Countries", len(selected_iso_codes))

    st.divider()

    st.subheader("Emissions Trend Over Time")
    st.caption("Evolution of annual CO2 emissions for the selected countries.")

    fig_trend = go.Figure()
    for idx, iso_code in enumerate(selected_iso_codes):
        df_c = df_t_filtered[df_t_filtered["ISOcode"] == iso_code].sort_values("Year")
        if df_c.empty:
            continue
        country_name = df_c["Country"].iloc[0]
        color = CLIMATE_QUALITATIVE[idx % len(CLIMATE_QUALITATIVE)]
        mode = "lines+markers" if len(selected_iso_codes) < 10 else "lines"
        fig_trend.add_trace(go.Scatter(
            x=df_c["Year"], y=df_c["CO2"],
            mode=mode, name=country_name,
            line=dict(color=color, width=2.2),
            marker=dict(size=4),
            hovertemplate=(
                f"<b>{country_name}</b><br>"
                "Year: %{x}<br>"
                "CO2: %{y:,.2f} Mt<extra></extra>"
            ),
        ))

    fig_trend.update_layout(
        template=PLOTLY_TEMPLATE,
        xaxis_title="Year",
        yaxis_title="CO2 Emissions (Mt)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=480,
        margin=CHART_MARGIN,
    )

    if show_events:
        events_sub = df_events[df_events["ISOcode"].isin(evt_iso_codes)]
        add_events_to_fig(fig_trend, events_sub, selected_iso_codes, year_range)

    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    st.subheader(f"Global Emissions Hierarchy ({latest_year})")
    df_co2_latest = df_t_filtered[df_t_filtered["Year"] == latest_year]
    df_capita_latest = df_c_filtered[
        (df_c_filtered["Year"] == latest_year)
        & (df_c_filtered["ISOcode"].isin(selected_iso_codes))
    ]

    df_tree = pd.merge(
        df_co2_latest[["Country", "CO2", "ISOcode"]],
        df_capita_latest[["ISOcode", "CO2_per_capita"]],
        on="ISOcode", how="inner",
    ).dropna(subset=["CO2", "CO2_per_capita"])

    tm_col1, tm_col2 = st.columns([1, 2])
    with tm_col1:
        size_mode = st.radio(
            "Size By:",
            ["Absolute", "Log Scale"],
            horizontal=True,
        )

    if not df_tree.empty:
        df_tree["CO2_log"] = np.log10(df_tree["CO2"].clip(lower=0.1) + 1)
    
    if size_mode == "Absolute":
        size_col = "CO2"
    else:
        size_col = "CO2_log"
    
    st.caption(
        "Rectangles are sized by total emissions. Color represents per-capita emissions."
    )

    if df_tree.empty:
        st.info("No matching data for the selected countries / year.")
    else:
        custom_scale = [
            CLIMATE_QUALITATIVE[2], 
            CLIMATE_QUALITATIVE[3], 
            CLIMATE_QUALITATIVE[1]
        ]
        
        fig_treemap = px.treemap(
            df_tree,
            path=["Country"],
            values=size_col,
            color="CO2_per_capita",
            color_continuous_scale=custom_scale,
            hover_data={"CO2": ":.1f", "CO2_per_capita": ":.2f"},
            labels={
                "CO2": "Total Emissions (Mt)",
                "CO2_per_capita": "Per Capita (t)"
            },
        )

        fig_treemap.update_coloraxes(
            cmin=0,
            cmid=df_tree["CO2_per_capita"].median(), 
            colorbar_title_text="Per Capita (t)",
            colorbar_thickness=15,
        )
        
        fig_treemap.update_layout(
            template=PLOTLY_TEMPLATE,
            margin=dict(l=10, r=10, t=10, b=10),
            height=500,
        )
        st.plotly_chart(fig_treemap, use_container_width=True)
