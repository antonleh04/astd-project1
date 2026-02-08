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
    df_land_area: pd.DataFrame,
    df_events: pd.DataFrame,
    selected_iso_codes: list[str],
    year_range: tuple[int, int],
    latest_year: int,
    show_events: bool,
    evt_iso_codes: list[str],
):
    """Render all charts for Tab 1 (The Big Picture)."""
    
    # ── KPI Metrics Row ──────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)

    avg_emissions = df_t_filtered["CO2"].mean()
    variance      = df_t_filtered["CO2"].var() if len(df_t_filtered) > 1 else 0

    latest_total = df_t_filtered[df_t_filtered["Year"] == latest_year]["CO2"].sum()
    prev_total   = df_t_filtered[df_t_filtered["Year"] == latest_year - 1]["CO2"].sum()
    yoy = ((latest_total - prev_total) / prev_total * 100) if prev_total else 0

    # delta_color="inverse" → green when emissions decrease (good for climate)
    m1.metric(
        "Latest Total", f"{latest_total:,.0f} Mt", f"{yoy:+.1f}% YoY",
        delta_color="inverse",
    )
    m2.metric("Avg Emission", f"{avg_emissions:,.1f} Mt")
    m3.metric("Variance", f"{variance:,.2e}")
    m4.metric("Countries", len(selected_iso_codes))

    st.divider()

    # ── Emissions trend (line chart) ─────────────────────────────────────────
    st.subheader("Emissions Trend Over Time")

    fig_trend = go.Figure()
    for idx, iso_code in enumerate(selected_iso_codes):
        df_c = df_t_filtered[df_t_filtered["ISOcode"] == iso_code].sort_values("Year")
        if df_c.empty:
            continue
        country_name = df_c["Country"].iloc[0]
        color = CLIMATE_QUALITATIVE[idx % len(CLIMATE_QUALITATIVE)]
        # Use markers only when there are few countries to keep the chart readable
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

    # Overlay historic events if the user toggled them on
    if show_events:
        events_sub = df_events[df_events["ISOcode"].isin(evt_iso_codes)]
        add_events_to_fig(fig_trend, events_sub, selected_iso_codes, year_range)

    st.plotly_chart(fig_trend, use_container_width=True)

    st.divider()

    # ── Treemap: land area sized, CO2 coloured ──────────────────────────────
    st.subheader(f"Emissions Treemap by Land Area ({latest_year})")
    st.caption(
        "Each rectangle is proportional to the country's land area; the colour "
        "intensity shows CO2 emissions on a **log scale**."
    )

    df_land_latest = df_land_area[
        (df_land_area["Year"] == latest_year)
        & (df_land_area["ISOcode"].isin(selected_iso_codes))
    ]
    df_co2_latest = df_t_filtered[df_t_filtered["Year"] == latest_year]

    df_tree = pd.merge(
        df_co2_latest[["Country", "CO2", "ISOcode"]],
        df_land_latest[["ISOcode", "Land area (sq. km)"]],
        on="ISOcode", how="inner",
    ).dropna(subset=["Land area (sq. km)", "CO2"])

    if df_tree.empty:
        st.info("No matching land-area data for the selected countries / year.")
    else:
        df_tree["CO2_log"] = np.log10(df_tree["CO2"].clip(lower=1))
        fig_treemap = px.treemap(
            df_tree,
            path=["Country"],
            values="Land area (sq. km)",
            color="CO2_log",
            color_continuous_scale="YlOrRd",
            hover_data={"CO2": ":.2f", "CO2_log": False},
            labels={"CO2_log": "CO2 (log)"},
        )
        fig_treemap.update_coloraxes(
            colorbar_title_text="CO2 (Mt, log\u2081\u2080)",
            colorbar_tickmode="array",
            colorbar_tickvals=np.log10([1, 10, 100, 1000, 10000]),
            colorbar_ticktext=["1", "10", "100", "1 k", "10 k"],
        )
        fig_treemap.update_layout(
            template=PLOTLY_TEMPLATE,
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_treemap, use_container_width=True)
