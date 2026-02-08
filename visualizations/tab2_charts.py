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

from config import CLIMATE_QUALITATIVE, COLORS, PLOTLY_TEMPLATE, CHART_MARGIN
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
        "Press Play to watch each country's path through emissions space over time. "
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
        # ── Build animated trajectory ──
        # Collect per-country data
        country_data = {}
        for idx, iso_code in enumerate(selected_iso_codes):
            df_country = df_traj[df_traj["ISOcode"] == iso_code].sort_values("Year")
            if df_country.empty:
                continue
            country_name = df_country["Country"].iloc[0]
            color = CLIMATE_QUALITATIVE[idx % len(CLIMATE_QUALITATIVE)]
            country_data[iso_code] = {
                "name": country_name,
                "color": color,
                "df": df_country.reset_index(drop=True),
            }

        if not country_data:
            st.info("No trajectory data available for the selected countries.")
        else:
            # Determine the union of all years across selected countries
            all_years = sorted(df_traj["Year"].unique())

            # ── Base figure: empty traces (one line + one head-marker per country) ──
            fig_traj = go.Figure()
            for iso_code, cdata in country_data.items():
                # Trajectory line (starts empty)
                fig_traj.add_trace(go.Scatter(
                    x=[], y=[],
                    mode="lines+markers",
                    name=cdata["name"],
                    line=dict(color=cdata["color"], width=2),
                    marker=dict(size=5, color=cdata["color"]),
                    hovertemplate=(
                        f"<b>{cdata['name']}</b><br>"
                        "Year: %{text}<br>"
                        "Per Capita: %{x:.2f} t/capita<br>"
                        "Total: %{y:,.2f} Mt<extra></extra>"
                    ),
                ))
                # Moving head marker (current year dot)
                fig_traj.add_trace(go.Scatter(
                    x=[], y=[],
                    mode="markers+text",
                    marker=dict(size=14, color=cdata["color"], symbol="diamond",
                                line=dict(width=2, color="white")),
                    textposition="top center",
                    textfont=dict(size=10, color=cdata["color"]),
                    showlegend=False,
                    hoverinfo="skip",
                ))

            # ── Build frames: each frame shows data up to that year ──
            frames = []
            for yi, year in enumerate(all_years):
                frame_data = []
                for iso_code, cdata in country_data.items():
                    df_c = cdata["df"]
                    df_up_to = df_c[df_c["Year"] <= year]

                    # Line trace (cumulative)
                    frame_data.append(go.Scatter(
                        x=df_up_to["CO2_per_capita"],
                        y=df_up_to["CO2"],
                        mode="lines+markers",
                        line=dict(color=cdata["color"], width=2),
                        marker=dict(size=5, color=cdata["color"]),
                        text=df_up_to["Year"],
                    ))

                    # Head marker (only the latest point up to this year)
                    if not df_up_to.empty:
                        last = df_up_to.iloc[-1]
                        frame_data.append(go.Scatter(
                            x=[last["CO2_per_capita"]],
                            y=[last["CO2"]],
                            mode="markers+text",
                            marker=dict(size=14, color=cdata["color"],
                                        symbol="diamond",
                                        line=dict(width=2, color="white")),
                            text=[f"{int(last['Year'])}"],
                            textposition="top center",
                            textfont=dict(size=10, color=cdata["color"]),
                        ))
                    else:
                        frame_data.append(go.Scatter(x=[], y=[]))

                frames.append(go.Frame(
                    data=frame_data,
                    name=str(int(year)),
                ))

            fig_traj.frames = frames

            # ── Axis ranges (fixed so the view doesn't jump) ──
            x_min = df_traj["CO2_per_capita"].min()
            x_max = df_traj["CO2_per_capita"].max()
            y_min = df_traj["CO2"].min()
            y_max = df_traj["CO2"].max()
            x_pad = (x_max - x_min) * 0.08 or 1
            y_pad = (y_max - y_min) * 0.08 or 1

            # ── Determine sensible animation speed ──
            n_years = len(all_years)
            frame_dur = max(40, min(300, int(10_000 / max(n_years, 1))))

            # ── Layout with Play / Pause / Slider ──
            fig_traj.update_layout(
                template=PLOTLY_TEMPLATE,
                xaxis=dict(
                    title="Per Capita Emissions (tonnes CO2 / capita)",
                    range=[x_min - x_pad, x_max + x_pad],
                    # Add standoff to ensure title doesn't hit buttons
                    title_standoff=20
                ),
                yaxis=dict(
                    title="Total Emissions (Mt CO2)",
                    range=[y_min - y_pad, y_max + y_pad],
                ),
                hovermode="closest",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1,
                ),
                height=600, # Increased height to accommodate the controls
                # Override margin to give generous space at bottom for slider
                margin=dict(l=50, r=50, t=50, b=130),
                updatemenus=[dict(
                    type="buttons",
                    showactive=False,
                    # Position buttons below the chart area (y < 0)
                    x=0.0, y=-0.25,
                    xanchor="left", yanchor="top",
                    pad={"r": 10, "t": 10},
                    buttons=[
                        dict(
                            label="▶ Play",
                            method="animate",
                            args=[
                                None,
                                dict(
                                    frame=dict(duration=frame_dur, redraw=True),
                                    fromcurrent=True,
                                    transition=dict(duration=frame_dur // 2,
                                                    easing="cubic-in-out"),
                                    mode="immediate",
                                ),
                            ],
                        ),
                        dict(
                            label="⏸ Pause",
                            method="animate",
                            args=[
                                [None],
                                dict(
                                    frame=dict(duration=0, redraw=False),
                                    mode="immediate",
                                ),
                            ],
                        ),
                    ],
                )],
                sliders=[dict(
                    active=0,
                    steps=[
                        dict(
                            args=[
                                [str(int(year))],
                                dict(
                                    frame=dict(duration=frame_dur, redraw=True),
                                    mode="immediate",
                                    transition=dict(duration=frame_dur // 2),
                                ),
                            ],
                            label=str(int(year)),
                            method="animate",
                        )
                        for year in all_years
                    ],
                    # Position slider next to buttons, also below chart
                    x=0.15, len=0.85,
                    xanchor="left",
                    y=-0.25, yanchor="top",
                    pad={"t": 0, "b": 10},
                    currentvalue=dict(
                        prefix="Year: ",
                        visible=True,
                        xanchor="center",
                    ),
                    transition=dict(duration=frame_dur // 2,
                                    easing="cubic-in-out"),
                )],
            )

            # Updated st.plotly_chart with config to fix modebar issues
            st.plotly_chart(
                fig_traj, 
                use_container_width=True,
                config={
                    'displayModeBar': False,  # Hide standard Plotly toolbar to prevent interaction bugs
                    'responsive': True        # Ensure chart adapts well to container resizing
                }
            )

            st.caption(
                "◆ Diamond marker follows the latest data point for each country. "
                "Use the slider to scrub to a specific year."
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
            "(need ≥ 10 overlapping years)."
        )
    else:
        # -- Dual-axis time-series overlay --
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(
            x=merged_ccf["Year"], y=merged_ccf["CO2_YoY_Change"],
            mode="lines+markers", name="CO2 YoY Change (%)",
            line=dict(color=COLORS["co2_change"], width=2), marker=dict(size=4),
        ))
        fig_ts.add_trace(go.Scatter(
            x=merged_ccf["Year"], y=merged_ccf["GDP Growth (annual %)"],
            mode="lines+markers", name="GDP Growth (%)",
            line=dict(color=COLORS["gdp_growth"], width=2), marker=dict(size=4),
            yaxis="y2",
        ))
        fig_ts.update_layout(
            template=PLOTLY_TEMPLATE, height=360, hovermode="x unified",
            xaxis=dict(title="Year"),
            yaxis=dict(
                title="CO2 YoY Change (%)",
                title_font=dict(color=COLORS["co2_change"]),
                tickfont=dict(color=COLORS["co2_change"]),
            ),
            yaxis2=dict(
                title="GDP Growth (%)",
                title_font=dict(color=COLORS["gdp_growth"]),
                tickfont=dict(color=COLORS["gdp_growth"]),
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
                    line=dict(color=COLORS["stem_line"], width=2),
                    showlegend=False, hoverinfo="skip",
                ))

            # Coloured markers on top of each stem
            colors_ccf = [
                COLORS["negative"] if c < 0 else COLORS["positive"] for c in ccf_subset
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
                y=0, line_dash="dash", line_color=COLORS["zero_line"], line_width=1,
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