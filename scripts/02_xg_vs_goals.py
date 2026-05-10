"""
Script 02 — xG vs Actual Goals
================================
Purpose: Visualise how each player's actual goals compare to their expected
         goals, making over/underperformance immediately visible.

Two charts are produced:
  1. Horizontal bar chart (xG vs Goals side-by-side) for top players
  2. Scatter plot (xG on x-axis, Goals on y-axis) with a y=x reference line.
     Points above the line = overperformers. Below = underperformers.

Reading the scatter:
  - The diagonal y=x line represents "exact expectation" — scoring exactly
    what xG predicted.
  - Positive xG diff: dots above line. Consistent upward drift = elite finisher.
  - Negative xG diff: dots below line. Can indicate poor finishing OR small sample.

Run: python scripts/02_xg_vs_goals.py
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

COMPETITION_ID = 43   # FIFA World Cup
SEASON_ID = 106       # 2022
N_MATCHES = 64        # full tournament

# ── Load (uses cached data from previous script run) ─────────────────────────
print("Loading events...")
matches = get_matches(COMPETITION_ID, SEASON_ID)
match_ids = matches["match_id"].head(N_MATCHES).tolist()
events = get_all_events(match_ids)
shots = get_shots(events)
summary = xg_per_player(shots)

# Only keep players with enough shots to be meaningful (>=3 shots)
summary_filtered = summary[summary["shots_taken"] >= 3].head(15)

# ── Chart 1: Side-by-side bar chart ──────────────────────────────────────────
# This is the most intuitive view — the gap between the blue (xG) and red (goals)
# bar is the over/underperformance. Taller red = overperformer.
print("Generating bar chart...")
fig = plot_xg_bar(summary_filtered, top_n=15, filename="01_xg_vs_goals_bar.png")
plt.close(fig)

# ── Chart 2: Scatter plot ─────────────────────────────────────────────────────
# Each dot is one player. The diagonal line is y=x (goals = xG).
# This reveals the *magnitude* of over/underperformance more clearly than bars.
print("Generating scatter plot...")

plot_data = summary[summary["shots_taken"] >= 3].copy()

fig2, ax = plt.subplots(figsize=(9, 7))

# Colour-code by xG diff: green = overperform, red = underperform, grey = neutral
colours = plot_data["xg_diff"].apply(
    lambda d: "#27ae60" if d > 0.3 else ("#e74c3c" if d < -0.3 else "#95a5a6")
)

scatter = ax.scatter(
    plot_data["xg"],
    plot_data["goals"],
    s=plot_data["shots_taken"] * 8,  # bubble size = number of shots
    c=colours,
    alpha=0.8,
    edgecolors="white",
    linewidths=0.6,
    zorder=3,
)

# Diagonal reference line: where xG == goals
max_val = max(plot_data["xg"].max(), plot_data["goals"].max()) + 0.5
ax.plot([0, max_val], [0, max_val], "--", color="#bdc3c7", linewidth=1.2, label="xG = Goals (expected)", zorder=2)

# Label the top players by name
top_by_xg = plot_data.nlargest(8, "xg")
for _, row in top_by_xg.iterrows():
    ax.annotate(
        row["player"].split()[-1],  # surname only to avoid crowding
        xy=(row["xg"], row["goals"]),
        xytext=(4, 4),
        textcoords="offset points",
        fontsize=7.5,
        color="#2c3e50",
    )

# Legend for colour
green_patch = mpatches.Patch(color="#27ae60", label="Overperformer (Goals > xG + 0.3)")
red_patch = mpatches.Patch(color="#e74c3c", label="Underperformer (Goals < xG − 0.3)")
grey_patch = mpatches.Patch(color="#95a5a6", label="Within expectation")
ax.legend(handles=[green_patch, red_patch, grey_patch], fontsize=8, loc="upper left")

ax.set_xlabel("Expected Goals (xG)", fontsize=11)
ax.set_ylabel("Actual Goals Scored", fontsize=11)
ax.set_title(
    "xG vs Actual Goals — La Liga 2015/16 (30 matches)\n"
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

# ── Print interpretation ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Interpretation Guide")
print("=" * 60)
print("  xG diff > 0 : Player scored MORE than expected (overperformer)")
print("  xG diff < 0 : Player scored FEWER than expected (underperformer)")
print("  Sample size matters: small xG diff over 3–5 shots = noise.")
print("  Large diff over 10+ shots starts to suggest a real signal.")

top_over = summary_filtered.nlargest(3, "xg_diff")
top_under = summary_filtered.nsmallest(3, "xg_diff")

print("\nTop 3 Overperformers:")
for _, r in top_over.iterrows():
    print(f"  {r['player']}: xG {r['xg']:.2f} → {int(r['goals'])} goals ({r['xg_diff']:+.2f})")

print("\nTop 3 Underperformers:")
for _, r in top_under.iterrows():
    print(f"  {r['player']}: xG {r['xg']:.2f} → {int(r['goals'])} goals ({r['xg_diff']:+.2f})")

print("\n✓ Analysis 2 complete. Proceed to scripts/03_defensive_metrics.py")
