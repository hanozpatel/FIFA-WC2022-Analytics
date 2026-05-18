"""
PPDA (Passes Allowed Per Defensive Action) per team.
Lower PPDA = more aggressive press; higher = deeper defensive shape.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
from src.data_loader import get_matches, get_all_events
from src.metrics import ppda_per_team

FIGURES_DIR = Path(__file__).parent.parent / "outputs" / "figures"
TABLES_DIR = Path(__file__).parent.parent / "outputs" / "tables"

COMPETITION_ID = 43
SEASON_ID = 106

print("Loading events (FIFA World Cup 2022, all 64 matches)...")
matches = get_matches(COMPETITION_ID, SEASON_ID)
match_ids = matches["match_id"].tolist()
events = get_all_events(match_ids)
print(f"  {len(events):,} events loaded.\n")

print("Computing PPDA per team...")
ppda = ppda_per_team(events)

print("=" * 78)
print("PPDA per Team — FIFA World Cup 2022  (↓ = more aggressive press)")
print("=" * 78)
print(f"{'Team':<28} {'Matches':>7} {'Def.Actions':>12} {'Opp.Passes':>11} {'PPDA':>6}")
print("-" * 78)
for _, r in ppda.iterrows():
    ppda_str = f"{r['ppda']:.2f}" if r["ppda"] is not None else "N/A"
    marker = " ◀ aggressive" if r["ppda"] is not None and r["ppda"] < ppda["ppda"].quantile(0.25) else ""
    print(
        f"{r['team']:<28} {int(r['matches']):>7} {int(r['defensive_actions']):>12} "
        f"{int(r['opponent_passes']):>11} {ppda_str:>6}{marker}"
    )

import pandas as pd
success_path = TABLES_DIR / "press_success_rate.csv"
if success_path.exists():
    success = pd.read_csv(success_path)
    combined = ppda.merge(success[["team", "success_rate_pct"]], on="team", how="left")
    corr = combined["ppda"].corr(combined["success_rate_pct"])
    print(f"\nCorrelation (PPDA vs press success rate): {corr:.3f}")
    if corr < -0.3:
        print("  → Teams with lower PPDA (more aggressive) tend to have HIGHER success rates.")
    elif corr > 0.3:
        print("  → Teams with lower PPDA tend to have LOWER success rates (press more, win less).")
    else:
        print("  → No strong linear relationship between PPDA and immediate press success rate.")

fig, ax = plt.subplots(figsize=(10, 9))
ppda_sorted = ppda.sort_values("ppda", ascending=False)

median_ppda = ppda["ppda"].median()
colours = ["#1a78cf" if v < median_ppda else "#f39c12" for v in ppda_sorted["ppda"]]

bars = ax.barh(ppda_sorted["team"], ppda_sorted["ppda"], color=colours, alpha=0.85, edgecolor="white")

for bar, val in zip(bars, ppda_sorted["ppda"]):
    ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}", va="center", fontsize=8.5)

ax.axvline(median_ppda, color="#2c3e50", linestyle="--", linewidth=1.2,
           label=f"Median PPDA: {median_ppda:.1f}")
ax.set_xlabel("PPDA (lower = more aggressive press)", fontsize=11)
ax.set_title(
    "PPDA per Team — FIFA World Cup 2022\n"
    "Blue = below median (more aggressive) | Orange = above median (deeper)",
    fontsize=12, fontweight="bold", pad=12
)
ax.legend(fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
ax.set_xlim(0, ppda_sorted["ppda"].max() * 1.12)

fig.tight_layout()
out_path = FIGURES_DIR / "06_ppda_per_team.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"\nSaved: {out_path}")
plt.close(fig)

ppda.to_csv(TABLES_DIR / "ppda_per_team.csv", index=False)
print(f"Saved: {TABLES_DIR / 'ppda_per_team.csv'}")
