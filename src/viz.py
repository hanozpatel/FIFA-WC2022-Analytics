"""
Visualisation helpers wrapping mplsoccer and matplotlib.

Every function saves its figure to outputs/figures/ and returns the figure
object so callers can do further customisation if needed.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from mplsoccer import Pitch, VerticalPitch
from pathlib import Path
import pandas as pd

FIGURES_DIR = Path(__file__).parent.parent / "outputs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def plot_xg_bar(xg_summary: pd.DataFrame, top_n: int = 15, filename: str = "xg_bar.png") -> plt.Figure:
    """Horizontal bar chart: xG vs goals for top-N players."""
    data = xg_summary.head(top_n).sort_values("xg")

    fig, ax = plt.subplots(figsize=(10, 7))
    y = range(len(data))
    bar_width = 0.35

    ax.barh([i - bar_width / 2 for i in y], data["xg"], height=bar_width, label="xG", color="#1a78cf", alpha=0.85)
    ax.barh([i + bar_width / 2 for i in y], data["goals"], height=bar_width, label="Actual Goals", color="#e84e1b", alpha=0.85)

    ax.set_yticks(list(y))
    ax.set_yticklabels(data["player"], fontsize=9)
    ax.set_xlabel("Value")
    ax.set_title(f"xG vs Goals — Top {top_n} Players by xG", fontsize=13, fontweight="bold", pad=12)
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / filename, dpi=150, bbox_inches="tight")
    print(f"Saved: {FIGURES_DIR / filename}")
    return fig


def plot_shot_map(shots: pd.DataFrame, player_name: str | None = None, filename: str = "shot_map.png") -> plt.Figure:
    """
    Plot shot locations on a half-pitch.

    Bubble size encodes xG value. Colour encodes outcome (goal vs no goal).
    """
    shots = shots.copy()

    # Filter to player if specified
    if player_name:
        shots = shots[shots["player"] == player_name]

    # Unpack location into x, y
    shots["x"] = shots["location"].apply(lambda loc: loc[0] if isinstance(loc, list) else None)
    shots["y"] = shots["location"].apply(lambda loc: loc[1] if isinstance(loc, list) else None)
    shots = shots.dropna(subset=["x", "y", "statsbomb_xg"])

    # Resolve outcome
    if shots["outcome"].dtype == object and shots["outcome"].apply(lambda x: isinstance(x, dict)).any():
        shots["outcome"] = shots["outcome"].apply(lambda x: x["name"] if isinstance(x, dict) else x)
    shots["is_goal"] = shots["outcome"] == "Goal"

    pitch = VerticalPitch(pitch_type="statsbomb", half=True, pitch_color="#1a1a2e", line_color="white")
    fig, ax = pitch.draw(figsize=(8, 6))

    # Non-goals
    non_goals = shots[~shots["is_goal"]]
    pitch.scatter(
        non_goals["x"], non_goals["y"],
        s=non_goals["statsbomb_xg"] * 800,
        c="#5BA4CF", alpha=0.6, edgecolors="white", linewidths=0.5,
        ax=ax, label="No Goal"
    )

    # Goals
    goals = shots[shots["is_goal"]]
    pitch.scatter(
        goals["x"], goals["y"],
        s=goals["statsbomb_xg"] * 800,
        c="#E84E1B", alpha=0.9, edgecolors="white", linewidths=0.8,
        marker="*", ax=ax, label="Goal"
    )

    title = f"Shot Map — {player_name}" if player_name else "Shot Map — All Players"
    ax.set_title(title, color="white", fontsize=12, fontweight="bold", pad=8)
    ax.legend(loc="lower center", facecolor="#1a1a2e", labelcolor="white", framealpha=0.6)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / filename, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved: {FIGURES_DIR / filename}")
    return fig


def plot_pressure_heatmap(pressures: pd.DataFrame, team_name: str | None = None, filename: str = "pressure_heatmap.png") -> plt.Figure:
    """
    Heatmap of where a team applies pressure on the pitch.

    High-intensity pressing teams will show concentration in the opponent half.
    """
    pressures = pressures.copy()
    if team_name:
        pressures = pressures[pressures["team"] == team_name]

    pressures["x"] = pressures["location"].apply(lambda loc: loc[0] if isinstance(loc, list) else None)
    pressures["y"] = pressures["location"].apply(lambda loc: loc[1] if isinstance(loc, list) else None)
    pressures = pressures.dropna(subset=["x", "y"])

    pitch = Pitch(pitch_type="statsbomb", pitch_color="#1a1a2e", line_color="white")
    fig, ax = pitch.draw(figsize=(12, 7))

    pitch.kdeplot(
        pressures["x"], pressures["y"],
        ax=ax,
        cmap="YlOrRd",
        fill=True,
        levels=100,
        alpha=0.7,
        thresh=0.02,
    )

    title = f"Pressure Heatmap — {team_name}" if team_name else "Pressure Heatmap — All Teams"
    ax.set_title(title, color="white", fontsize=13, fontweight="bold", pad=10)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / filename, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved: {FIGURES_DIR / filename}")
    return fig
