"""
Plot registry. Each entry exposes a title/description for the catalog and a
`compute` callable that returns a Plotly figure as a JSON-serialisable dict.

The compute functions here are placeholders that return a small demo figure.
Replace each one with a call into the real analytics pipeline. The web layer
treats them as opaque: as long as they return Plotly JSON, the frontend will
render them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List
import json

import plotly.graph_objects as go


@dataclass(frozen=True)
class PlotDef:
    key: str
    title: str
    description: str
    compute: Callable[[Path], dict]


def _placeholder(title: str, note: str) -> dict:
    fig = go.Figure()
    fig.add_annotation(
        text=f"{note}<br><sub>Wire this to the analytics pipeline.</sub>",
        showarrow=False,
        font=dict(size=14),
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
    )
    fig.update_layout(
        title=title,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=20, r=20, t=50, b=20),
        height=420,
    )
    return json.loads(fig.to_json())


def _shot_map(video_path: Path) -> dict:
    """Demo shot map: attacking-half pitch with synthetic shots sized by xG."""
    # StatsBomb-style coordinates: 120x80 pitch. We render the attacking half (x: 60..120).
    shots = [
        # (x, y, xg, minute, player, goal)
        (112, 40, 0.78, 9, "Messi", True),
        (108, 44, 0.31, 14, "Di María", False),
        (104, 36, 0.18, 22, "Álvarez", True),
        (115, 38, 0.62, 28, "Messi", False),
        (96, 50, 0.07, 33, "De Paul", False),
        (110, 32, 0.24, 41, "Mac Allister", False),
        (118, 41, 0.51, 47, "Álvarez", True),
        (102, 28, 0.09, 53, "Molina", False),
        (107, 45, 0.22, 58, "Messi", False),
        (113, 39, 0.44, 64, "Di María", True),
        (89, 40, 0.04, 71, "Fernández", False),
        (116, 36, 0.71, 78, "Álvarez", False),
        (105, 52, 0.12, 84, "Messi", True),
        (110, 30, 0.19, 88, "Mac Allister", False),
        (100, 47, 0.08, 92, "Lautaro", False),
    ]

    goals = [s for s in shots if s[5]]
    misses = [s for s in shots if not s[5]]

    def _trace(items, name, color, symbol):
        return go.Scatter(
            x=[s[0] for s in items],
            y=[s[1] for s in items],
            mode="markers",
            name=name,
            marker=dict(
                size=[10 + s[2] * 60 for s in items],
                color=color,
                line=dict(width=1.5, color="white"),
                symbol=symbol,
                opacity=0.85,
            ),
            customdata=[[s[3], s[4], s[2]] for s in items],
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
                "Minute: %{customdata[0]}'<br>"
                "xG: %{customdata[2]:.2f}<extra></extra>"
            ),
        )

    fig = go.Figure(
        data=[
            _trace(misses, "Shot", "#f59e0b", "circle"),
            _trace(goals, "Goal", "#22c55e", "star"),
        ]
    )

    line = dict(color="rgba(226,232,240,0.55)", width=1.5)

    # Pitch boundary (attacking half), penalty area, six-yard box, goal.
    shapes = [
        dict(type="rect", x0=60, y0=0, x1=120, y1=80, line=line),
        dict(type="rect", x0=102, y0=18, x1=120, y1=62, line=line),
        dict(type="rect", x0=114, y0=30, x1=120, y1=50, line=line),
        dict(type="rect", x0=120, y0=36, x1=121.5, y1=44,
             line=dict(color="#22c55e", width=2), fillcolor="rgba(34,197,94,0.25)"),
        # Halfway line + centre circle arc (right half only).
        dict(type="line", x0=60, y0=0, x1=60, y1=80, line=line),
        dict(type="circle", x0=50, y0=30, x1=70, y1=50, line=line),
        # Penalty spot.
        dict(type="circle", x0=107.7, y0=39.7, x1=108.3, y1=40.3,
             line=dict(color="rgba(226,232,240,0.7)"), fillcolor="rgba(226,232,240,0.7)"),
    ]

    fig.update_layout(
        title="Shot Map — Argentina (attacking half)",
        shapes=shapes,
        xaxis=dict(range=[58, 124], visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(range=[-2, 82], visible=False),
        legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"),
        margin=dict(l=10, r=10, t=50, b=10),
        height=460,
        plot_bgcolor="rgba(16,32,24,0.35)",
    )
    return json.loads(fig.to_json())


def _pass_network(video_path: Path) -> dict:
    return _placeholder("Pass Network", "Player nodes weighted by pass volume")


def _pressure_heatmap(video_path: Path) -> dict:
    return _placeholder("Pressure Heatmap", "Defensive pressure density on pitch")


def _xg_timeline(video_path: Path) -> dict:
    return _placeholder("xG Timeline", "Cumulative xG over the match clock")


def _possession_share(video_path: Path) -> dict:
    return _placeholder("Possession Share", "Possession % over rolling windows")


_REGISTRY: Dict[str, PlotDef] = {
    p.key: p
    for p in [
        PlotDef("shot_map", "Shot Map", "Shot locations and xG.", _shot_map),
        PlotDef("pass_network", "Pass Network", "Pass connections between players.", _pass_network),
        PlotDef("pressure_heatmap", "Pressure Heatmap", "Defensive pressure density.", _pressure_heatmap),
        PlotDef("xg_timeline", "xG Timeline", "Cumulative xG over time.", _xg_timeline),
        PlotDef("possession_share", "Possession Share", "Rolling possession share.", _possession_share),
    ]
}


def list_plots() -> List[PlotDef]:
    return list(_REGISTRY.values())


def get_plot(key: str) -> PlotDef | None:
    return _REGISTRY.get(key)
