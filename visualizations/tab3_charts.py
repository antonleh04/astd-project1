"""
Tab 3 Charts: Sectoral Deep Dive
=================================
Visualizations for sector composition and fingerprints.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import CLIMATE_QUALITATIVE, PLOTLY_TEMPLATE
from utils import add_events_to_fig


def render_tab3_charts(
    df_s_filtered: pd.DataFrame,
    df_events: pd.DataFrame,
    selected_countries: list[str],
    year_range: tuple[int, int],
    latest_year: int,
    show_events: bool,
    evt_cats: list[str],
):
    """Render all charts for Tab 3 (Sectoral Deep Dive)."""
    
    # ── Stacked area: sector composition for one country ─────────────────────
    st.subheader("Sector Composition Over Time")

    if len(selected_countries) == 1:
        focus_country = selected_countries[0]
    else:
        focus_country = st.selectbox(
            "Focus country for stacked area chart",
            selected_countries, key="sector_focus",
        )

    df_focus = df_s_filtered[df_s_filtered["Country"] == focus_country]

    if df_focus.empty:
        st.info(f"No sector data for **{focus_country}** in this range.")
    else:
        sector_ts = df_focus.groupby(["Year", "Sector"])["CO2"].sum().reset_index()
        fig_area = go.Figure()
        sectors = sorted(sector_ts["Sector"].unique())
        for idx, sec in enumerate(sectors):
            df_sec = sector_ts[sector_ts["Sector"] == sec].sort_values("Year")
            color = CLIMATE_QUALITATIVE[idx % len(CLIMATE_QUALITATIVE)]
            fig_area.add_trace(go.Scatter(
                x=df_sec["Year"], y=df_sec["CO2"],
                mode="lines", name=sec, stackgroup="one",
                line=dict(width=0.5, color=color),
                hovertemplate=(
                    f"<b>{sec}</b><br>"
                    "Year: %{x}<br>"
                    "CO2: %{y:,.2f} Mt<extra></extra>"
                ),
            ))
        fig_area.update_layout(
            template=PLOTLY_TEMPLATE,
            title=f"Sectoral Emissions \u2014 {focus_country}",
            xaxis_title="Year",
            yaxis_title="CO2 Emissions (Mt)",
            hovermode="x unified",
            height=460,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
            ),
            margin=dict(l=50, r=30, t=60, b=50),
        )

        if show_events:
            events_sub = df_events[df_events["Country"].isin(evt_cats)]
            add_events_to_fig(fig_area, events_sub, [focus_country], year_range)

        st.plotly_chart(fig_area, use_container_width=True)

    st.divider()

    # ── Sectoral Fingerprint Treemap ─────────────────────────────────────────
    st.subheader(f"Sectoral Fingerprint ({latest_year})")
    st.markdown("##### Sector Breakdown Treemap")
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
