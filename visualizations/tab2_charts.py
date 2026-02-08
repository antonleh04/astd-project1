"""
Tab 2 Charts: Equity & Economy
===============================
Visualizations for emissions trajectory and cross-correlation analysis.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from statsmodels.tsa.stattools import ccf

from config import CLIMATE_QUALITATIVE, PLOTLY_TEMPLATE, CHART_MARGIN
from utils import add_events_to_fig


def render_tab2_charts(
    df_t_filtered: pd.DataFrame,
    df_c_filtered: pd.DataFrame,
    df_totals: pd.DataFrame,
    df_gdp_growth: pd.DataFrame,
    df_events: pd.DataFrame,
    selected_iso_codes: list[str],
    year_range: tuple[int, int],
    show_events: bool,
    evt_iso_codes: list[str],
):
    """Render all charts for Tab 2 (Equity & Economy)."""
    
    # ── Emissions Trajectory: Per Capita vs Total ────────────────────────────
    st.subheader("Emissions Trajectory: Per Capita vs Total")
    st.caption(
        "Follow each country's path through emissions space over time. "
        "The trajectory shows how total and per-capita emissions evolve together."
    )

    # Merge total and per-capita data for the selected countries and years
    df_traj = pd.merge(
        df_t_filtered[["ISOcode", "Country", "Year", "CO2"]],
        df_c_filtered[["ISOcode", "Year", "CO2_per_capita"]],
        on=["ISOcode", "Year"], how="inner",
    ).sort_values(["ISOcode", "Year"])

    if df_traj.empty:
        st.info("No combined trajectory data for selected countries.")
    else:
        fig_traj = go.Figure()
        
        for idx, iso_code in enumerate(selected_iso_codes):
            df_country = df_traj[df_traj["ISOcode"] == iso_code].sort_values("Year")
            if df_country.empty:
                continue
            
            country_name = df_country["Country"].iloc[0]
            color = CLIMATE_QUALITATIVE[idx % len(CLIMATE_QUALITATIVE)]
            
            # Add the trajectory line with markers
            fig_traj.add_trace(go.Scatter(
                x=df_country["CO2_per_capita"],
                y=df_country["CO2"],
                mode="lines+markers",
                name=country_name,
                line=dict(color=color, width=2),
                marker=dict(size=6, color=color),
                text=df_country["Year"],
                hovertemplate=(
                    f"<b>{country_name}</b><br>"
                    "Year: %{text}<br>"
                    "Per Capita: %{x:.2f} t/capita<br>"
                    "Total: %{y:,.2f} Mt<extra></extra>"
                ),
            ))
            
            # Add start and end markers for clarity
            if len(df_country) > 0:
                # Start marker (earliest year)
                start_row = df_country.iloc[0]
                fig_traj.add_trace(go.Scatter(
                    x=[start_row["CO2_per_capita"]],
                    y=[start_row["CO2"]],
                    mode="markers+text",
                    marker=dict(size=12, color=color, symbol="circle", 
                               line=dict(width=2, color="white")),
                    text=[f"{start_row['Year']:.0f}"],
                    textposition="top center",
                    textfont=dict(size=9, color=color),
                    showlegend=False,
                    hoverinfo="skip",
                ))
                
                # End marker (latest year)
                end_row = df_country.iloc[-1]
                fig_traj.add_trace(go.Scatter(
                    x=[end_row["CO2_per_capita"]],
                    y=[end_row["CO2"]],
                    mode="markers+text",
                    marker=dict(size=12, color=color, symbol="diamond",
                               line=dict(width=2, color="white")),
                    text=[f"{end_row['Year']:.0f}"],
                    textposition="bottom center",
                    textfont=dict(size=9, color=color),
                    showlegend=False,
                    hoverinfo="skip",
                ))
        
        fig_traj.update_layout(
            template=PLOTLY_TEMPLATE,
            xaxis_title="Per Capita Emissions (tonnes CO2 / capita)",
            yaxis_title="Total Emissions (Mt CO2)",
            hovermode="closest",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
            ),
            height=520,
            margin=CHART_MARGIN,
        )
        
        st.plotly_chart(fig_traj, use_container_width=True)
        
        st.caption(
            "⚫ Circle = start year  ◆ Diamond = end year. "
            "Arrows along the trajectory show the direction of time."
        )

    st.divider()

    # ── Cross-Correlation: GDP Growth vs CO2 Change ──────────────────────────
    st.subheader("Cross-Correlation: GDP Growth vs CO2 Change")
    st.caption(
        "Analyse the temporal relationship between economic growth and emissions "
        "changes.  Negative lags mean GDP *leads* CO2; positive lags mean CO2 "
        "changes *precede* GDP."
    )

    # Country picker (skip if only one country selected)
    if len(selected_iso_codes) == 1:
        analysis_iso = selected_iso_codes[0]
    else:
        # Create a mapping for display
        iso_to_name = df_totals[["ISOcode", "Country"]].drop_duplicates().set_index("ISOcode")["Country"].to_dict()
        analysis_iso = st.selectbox(
            "Select Country for Analysis",
            selected_iso_codes,
            format_func=lambda iso: iso_to_name.get(iso, iso),
            key="ccf_country",
        )

    # Build aligned CO2-YoY-change and GDP-growth series
    co2_country = (
        df_totals[df_totals["ISOcode"] == analysis_iso][["Year", "CO2"]]
        .sort_values("Year").dropna()
    )
    co2_country["CO2_YoY_Change"] = co2_country["CO2"].pct_change() * 100

    gdp_country = (
        df_gdp_growth[df_gdp_growth["ISOcode"] == analysis_iso]
        [["Year", "GDP Growth (annual %)"]]
        .sort_values("Year").dropna()
    )

    merged_ccf = pd.merge(
        co2_country[["Year", "CO2_YoY_Change"]],
        gdp_country[["Year", "GDP Growth (annual %)"]],
        on="Year", how="inner",
    ).dropna()
    
    analysis_country_name = df_totals[df_totals["ISOcode"] == analysis_iso]["Country"].iloc[0] if not df_totals[df_totals["ISOcode"] == analysis_iso].empty else analysis_iso

    if len(merged_ccf) < 10:
        st.warning(
            f"Insufficient data for **{analysis_country_name}** "
            "(need \u2265 10 overlapping years)."
        )
    else:
        # -- Dual-axis time-series overlay --
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(
            x=merged_ccf["Year"], y=merged_ccf["CO2_YoY_Change"],
            mode="lines+markers", name="CO2 YoY Change (%)",
            line=dict(color="#E85D3A", width=2), marker=dict(size=4),
        ))
        fig_ts.add_trace(go.Scatter(
            x=merged_ccf["Year"], y=merged_ccf["GDP Growth (annual %)"],
            mode="lines+markers", name="GDP Growth (%)",
            line=dict(color="#4A90D9", width=2), marker=dict(size=4),
            yaxis="y2",
        ))
        fig_ts.update_layout(
            template=PLOTLY_TEMPLATE, height=360, hovermode="x unified",
            xaxis=dict(title="Year"),
            yaxis=dict(
                title="CO2 YoY Change (%)",
                title_font=dict(color="#E85D3A"),
                tickfont=dict(color="#E85D3A"),
            ),
            yaxis2=dict(
                title="GDP Growth (%)",
                title_font=dict(color="#4A90D9"),
                tickfont=dict(color="#4A90D9"),
                overlaying="y", side="right",
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
            ),
            margin=dict(l=50, r=50, t=30, b=40),
        )

        if show_events:
            events_sub = df_events[df_events["ISOcode"].isin(evt_iso_codes)]
            add_events_to_fig(fig_ts, events_sub, [analysis_iso], year_range)

        st.plotly_chart(fig_ts, use_container_width=True)

        # -- CCF lollipop chart --
        max_possible_lag = min(10, len(merged_ccf) // 3)
        max_lag = st.slider(
            "Max Lag (years)", 1, max_possible_lag,
            min(5, max_possible_lag), key="ccf_lag",
        )

        gdp_series = merged_ccf["GDP Growth (annual %)"].values
        co2_series = merged_ccf["CO2_YoY_Change"].values

        try:
            ccf_pos = ccf(co2_series, gdp_series, adjusted=False)

            # Build symmetric lag array [-max_lag ... +max_lag]
            lags = np.arange(-max_lag, max_lag + 1)
            ccf_subset: list[float] = []
            for lag in lags:
                if lag < 0:
                    # Negative lag: swap the series order
                    ccf_subset.append(
                        ccf(gdp_series, co2_series, adjusted=False)[abs(lag)]
                    )
                else:
                    ccf_subset.append(ccf_pos[lag])

            # Draw stem (stick) for each lag value
            fig_ccf = go.Figure()
            for lag_v, corr_v in zip(lags, ccf_subset):
                fig_ccf.add_trace(go.Scatter(
                    x=[lag_v, lag_v], y=[0, corr_v],
                    mode="lines",
                    line=dict(color="#c5d8cf", width=2),
                    showlegend=False, hoverinfo="skip",
                ))

            # Coloured markers on top of each stem
            colors_ccf = [
                "#E85D3A" if c < 0 else "#2E8B57" for c in ccf_subset
            ]
            fig_ccf.add_trace(go.Scatter(
                x=lags, y=ccf_subset, mode="markers",
                marker=dict(
                    size=12, color=colors_ccf,
                    line=dict(width=1, color="white"),
                ),
                name="Correlation",
                hovertemplate="<b>Lag %{x} yr</b><br>r = %{y:.3f}<extra></extra>",
            ))
            fig_ccf.add_hline(
                y=0, line_dash="dash", line_color="#708090", line_width=1,
            )
            fig_ccf.update_layout(
                template=PLOTLY_TEMPLATE, height=420, showlegend=False,
                xaxis=dict(title="Lag (years)", tickmode="linear", dtick=1),
                yaxis_title="Correlation Coefficient",
                margin=CHART_MARGIN,
            )
            st.plotly_chart(fig_ccf, use_container_width=True)

            # Interpret the peak automatically
            peak_idx  = int(np.argmax(np.abs(ccf_subset)))
            peak_lag  = int(lags[peak_idx])
            peak_corr = ccf_subset[peak_idx]

            if peak_lag == 0:
                interp = (
                    f"**Peak at Lag 0** (r = {peak_corr:.3f}): "
                    "GDP and CO2 changes are **synchronous**."
                )
            elif peak_lag < 0:
                interp = (
                    f"**Peak at Lag {peak_lag}** (r = {peak_corr:.3f}): "
                    f"GDP growth **leads** CO2 by {abs(peak_lag)} year(s)."
                )
            else:
                interp = (
                    f"**Peak at Lag +{peak_lag}** (r = {peak_corr:.3f}): "
                    f"CO2 changes **lead** GDP by {peak_lag} year(s)."
                )
            st.info(interp)

        except Exception as e:
            st.error(f"Cross-correlation error: {e}")
