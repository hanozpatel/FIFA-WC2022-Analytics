"""
Script 01 — xG per Player
==========================
Purpose: Calculate cumulative xG per player across the FIFA World Cup 2022,
         identify who generated the highest-quality chances, and save
         the result as a CSV table for use in the next analysis.

We use all 64 matches — the full tournament. This gives enough shots per
top player (Mbappé, Messi, Giroud) to draw meaningful conclusions.

Run: python scripts/01_xg_per_player.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import get_matches, get_all_events, get_shots
from src.metrics import xg_per_player

TABLES_DIR = Path(__file__).parent.parent / "outputs" / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

# ── Config ────────────────────────────────────────────────────────────────────
COMPETITION_ID = 43   # FIFA World Cup
SEASON_ID = 106       # 2022
N_MATCHES = 64        # full tournament

# ── Load data ─────────────────────────────────────────────────────────────────
print(f"Loading matches (FIFA World Cup 2022, all {N_MATCHES} matches)...")
matches = get_matches(COMPETITION_ID, SEASON_ID)
match_ids = matches["match_id"].head(N_MATCHES).tolist()

print(f"Fetching events for {len(match_ids)} matches (cached after first run)...")
events = get_all_events(match_ids)
shots = get_shots(events)
print(f"  {len(shots)} shot events loaded.\n")

# ── Calculate xG per player ───────────────────────────────────────────────────
# xg_per_player() in src/metrics.py:
#   - Groups by player name
#   - Sums statsbomb_xg (StatsBomb's model value, pre-computed per shot)
#   - Counts shots where outcome == 'Goal'
#   - Computes xg_diff = goals - xg  (positive = overperformer, negative = underperformer)
summary = xg_per_player(shots)

# ── Print results ─────────────────────────────────────────────────────────────
print("=" * 70)
print("xG Summary — Top 20 Players by Cumulative xG")
print("=" * 70)
print(f"{'Player':<30} {'Shots':>6} {'xG':>7} {'Goals':>6} {'xG/Shot':>8} {'xG Diff':>8}")
print("-" * 70)
for _, row in summary.head(20).iterrows():
    print(
        f"{row['player']:<30} {int(row['shots_taken']):>6} {row['xg']:>7.2f} "
        f"{int(row['goals']):>6} {row['xg_per_shot']:>8.3f} {row['xg_diff']:>+8.2f}"
    )
print("-" * 70)

# ── Highlight over/underperformers ────────────────────────────────────────────
# xg_diff > 0: scored more than expected (good finisher, or lucky)
# xg_diff < 0: scored fewer than expected (bad finisher, or unlucky)
overperformers = summary[summary["xg_diff"] > 0].head(5)
underperformers = summary[summary["xg_diff"] < -0.5].head(5)

print("\nTop 5 Overperformers (goals > xG):")
for _, r in overperformers.iterrows():
    print(f"  {r['player']:<30} xG: {r['xg']:.2f}  Goals: {int(r['goals'])}  Diff: {r['xg_diff']:+.2f}")

print("\nTop 5 Underperformers (goals < xG by >0.5):")
for _, r in underperformers.iterrows():
    print(f"  {r['player']:<30} xG: {r['xg']:.2f}  Goals: {int(r['goals'])}  Diff: {r['xg_diff']:+.2f}")

# ── Save output ───────────────────────────────────────────────────────────────
out_path = TABLES_DIR / "xg_per_player.csv"
summary.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")
print("\n✓ Analysis 1 complete. Proceed to scripts/02_xg_vs_goals.py")
