"""
Visualise how each player's actual goals compare to their expected goals.
Two charts: a horizontal bar chart (xG vs goals side-by-side) and a scatter
plot with y=x reference line (above = overperformer, below = underperformer).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from src.data_loader import get_matches, get_all_events, get_shots
from src.metrics import xg_per_player
from src.viz import plot_xg_bar

FIGURES_DIR = Path(__file__).parent.parent / "outputs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

COMPETITION_ID = 43
SEASON_ID = 106
N_MATCHES = 64

print("Loading events...")
matches = get_matches(COMPETITION_ID, SEASON_ID)
match_ids = matches["match_id"].head(N_MATCHES).tolist()
events = get_all_events(match_ids)
shots = get_shots(events)
summary = xg_per_player(shots)

summary_filtered = summary[summary["shots_taken"] >= 3].head(15)

print("Generating bar chart...")
fig = plot_xg_bar(summary_filtered, top_n=15, filename="01_xg_vs_goals_bar.png")
plt.close(fig)

print("Generating scatter plot...")

plot_data = summary[summary["shots_taken"] >= 3].copy()

fig2, ax = plt.subplots(figsize=(9, 7))

colours = plot_data["xg_diff"].apply(
    lambda d: "#27ae60" if d > 0.3 else ("#e74c3c" if d < -0.3 else "#95a5a6")
)

scatter = ax.scatter(
    plot_data["xg"],
    plot_data["goals"],
    s=plot_data["shots_taken"] * 8,
    c=colours,
    alpha=0.8,
    edgecolors="white",
    linewidths=0.6,
    zorder=3,
)

max_val = max(plot_data["xg"].max(), plot_data["goals"].max()) + 0.5
ax.plot([0, max_val], [0, max_val], "--", color="#bdc3c7", linewidth=1.2, label="xG = Goals (expected)", zorder=2)

top_by_xg = plot_data.nlargest(8, "xg")
for _, row in top_by_xg.iterrows():
    ax.annotate(
        row["player"].split()[-1],
        xy=(row["xg"], row["goals"]),
        xytext=(4, 4),
        textcoords="offset points",
        fontsize=7.5,
        color="#2c3e50",
    )

green_patch = mpatches.Patch(color="#27ae60", label="Overperformer (Goals > xG + 0.3)")
red_patch = mpatches.Patch(color="#e74c3c", label="Underperformer (Goals < xG − 0.3)")
grey_patch = mpatches.Patch(color="#95a5a6", label="Within expectation")
ax.legend(handles=[green_patch, red_patch, grey_patch], fontsize=8, loc="upper left")

ax.set_xlabel("Expected Goals (xG)", fontsize=11)
ax.set_ylabel("Actual Goals Scored", fontsize=11)
ax.set_title(
    "xG vs Actual Goals — FIFA World Cup 2022 (64 matches)\n"
    "Bubble size = number of shots taken",
    fontsize=12, fontweight="bold", pad=12,
)
ax.spines[["top", "right"]].set_visible(False)
ax.set_xlim(left=0)
ax.set_ylim(bottom=0)

fig2.tight_layout()
out_path = FIGURES_DIR / "02_xg_vs_goals_scatter.png"
fig2.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"Saved: {out_path}")
plt.close(fig2)

top_over = summary_filtered.nlargest(3, "xg_diff")
top_under = summary_filtered.nsmallest(3, "xg_diff")

print("\nTop 3 Overperformers:")
for _, r in top_over.iterrows():
    print(f"  {r['player']}: xG {r['xg']:.2f} → {int(r['goals'])} goals ({r['xg_diff']:+.2f})")

print("\nTop 3 Underperformers:")
for _, r in top_under.iterrows():
    print(f"  {r['player']}: xG {r['xg']:.2f} → {int(r['goals'])} goals ({r['xg_diff']:+.2f})")
