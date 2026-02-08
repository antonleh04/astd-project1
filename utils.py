"""
Utility Functions
=================
Helper functions for event filtering and annotation.
"""

import pandas as pd
import plotly.graph_objects as go


# =============================================================================
# EVENT HELPERS
# =============================================================================

def filter_events(
    events_df: pd.DataFrame,
    selected_countries: list[str],
    year_range: tuple[int, int],
) -> pd.DataFrame:
    """Return events that are either global or belong to one of the selected
    countries and fall within the chosen year range."""
    global_mask = events_df["Country"].isin(["Global", "World"])
    local_mask  = events_df["Country"].isin(selected_countries)
    year_mask   = events_df["Year"].between(*year_range)
    return events_df[(global_mask | local_mask) & year_mask]


def add_events_to_fig(
    fig: go.Figure,
    events_df: pd.DataFrame,
    selected_countries: list[str],
    year_range: tuple[int, int],
) -> None:
    """Overlay staggered, colour-coded event annotations on a Plotly figure.
    Annotations cycle through five vertical offsets to reduce overlap."""
    filtered = filter_events(events_df, selected_countries, year_range)
    if filtered.empty:
        return

    # Stagger annotations vertically so they don't pile up
    y_positions = [0.95, 0.85, 0.75, 0.65, 0.55]

    for i, (_, event) in enumerate(filtered.iterrows()):
        is_global  = event["Country"] in ["Global", "World"]
        icon       = "\U0001F30D" if is_global else "\U0001F4CD"
        line_color = "#4A90D9" if is_global else "#E85D3A"
        y_ref      = y_positions[i % len(y_positions)]

        fig.add_vline(
            x=event["Year"], line_width=1.2, line_dash="dot",
            line_color=line_color, opacity=0.55,
        )
        fig.add_annotation(
            x=event["Year"], y=y_ref, yref="paper",
            text=f"{icon} {event['Event']}",
            showarrow=True, arrowhead=2, arrowsize=0.8,
            arrowwidth=1, arrowcolor=line_color,
            ax=20, ay=-20,
            font=dict(size=9, color=line_color),
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor=line_color, borderwidth=1, borderpad=3,
            hovertext=(
                f"<b>{event['Event']} ({event['Year']})</b><br>"
                f"<i>{event['Country']}</i><br>{event['Description']}"
            ),
        )
