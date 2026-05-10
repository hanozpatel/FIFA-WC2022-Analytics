"""
Script 06 — PPDA (Passes Allowed Per Defensive Action)
=========================================================
Purpose: Calculate PPDA per team — one of the most widely used pressing
         efficiency metrics in football analytics research.

Formula:
  PPDA = opponent_passes / (pressures + interceptions + tackles)

Interpretation:
  - PPDA = 8  → for every 8 passes the opponent completes, you make 1 defensive action
  - PPDA = 15 → you allow 15 passes before acting — a much deeper, passive block
  - LOWER PPDA = more aggressive press | HIGHER PPDA = deeper defensive shape

Why this is better than raw pressures:
  Pressures per 90 measures effort. PPDA measures *efficiency* — how many passes
  you allow before you act. A team that presses but intercepts nothing has a high
  PPDA; a team that makes every press count has a low one.

Academic reference:
  The metric was popularised by Colin Trainor (StatsBomb) and Michael Caley.
  It is used as a standard pressing metric in academic studies on pressing
  intensity (e.g. Andrienko et al. 2019, Forcher et al. 2022).

Run: python scripts/06_ppda.py
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

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading events (FIFA World Cup 2022, all 64 matches)...")
matches = get_matches(COMPETITION_ID, SEASON_ID)
match_ids = matches["match_id"].tolist()
events = get_all_events(match_ids)
print(f"  {len(events):,} events loaded.\n")

# ── Calculate PPDA ────────────────────────────────────────────────────────────
# This iterates once per team (~32 teams), doing a couple of groupby operations
# each time — takes a few seconds.
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

# ── Compare PPDA vs press success rate from script 05 ────────────────────────
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

# ── Chart: PPDA horizontal bar chart ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 9))
ppda_sorted = ppda.sort_values("ppda", ascending=False)

# Colour: blue = low PPDA (aggressive), orange = high PPDA (passive)
median_ppda = ppda["ppda"].median()
colours = ["#1a78cf" if v < median_ppda else "#f39c12" for v in ppda_sorted["ppda"]]

bars = ax.barh(ppda_sorted["team"], ppda_sorted["ppda"], color=colours, alpha=0.85, edgecolor="white")

# Value labels on bars
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

# ── Save table ────────────────────────────────────────────────────────────────
ppda.to_csv(TABLES_DIR / "ppda_per_team.csv", index=False)
print(f"Saved: {TABLES_DIR / 'ppda_per_team.csv'}")

print("\n✓ Analysis 6 complete. Proceed to scripts/07_match_state.py")
