"""
Script 04 — Pitch Map Visualisations
======================================
Purpose: Place our data in spatial context by drawing results directly on a
         football pitch. Two maps are produced:

  1. Messi's shot map (World Cup 2022) — bubble size = xG, colour = outcome.
     Shows which areas he shot from and the quality of each attempt.

  2. Japan vs England pressure heatmap — side-by-side comparison of WHERE
     each team pressed. Japan (highest P/90) vs England (lowest P/90) makes
     the stylistic contrast maximally visible.

Why spatial visualisation matters for research:
  Event-level coordinates are what separate modern football analytics from
  traditional box-score stats. Pressing volume tells you HOW MUCH; the pitch
  map tells you WHERE and WHY — which defensive shape the team is executing.

Library: mplsoccer (wraps matplotlib, provides StatsBomb-scaled pitch objects).

Run: python scripts/04_pitch_map.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import get_matches, get_all_events, get_shots, get_pressures
from src.viz import plot_shot_map, plot_pressure_heatmap

COMPETITION_ID = 43   # FIFA World Cup
SEASON_ID = 106       # 2022

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading events (FIFA World Cup 2022, all 64 matches)...")
matches = get_matches(COMPETITION_ID, SEASON_ID)
match_ids = matches["match_id"].tolist()
events = get_all_events(match_ids)
shots = get_shots(events)
pressures = get_pressures(events)
print(f"  {len(shots)} shots, {len(pressures):,} pressures loaded.\n")

# ── Map 1: Messi shot map ─────────────────────────────────────────────────────
# Messi took 34 shots — the most of any player. His shot map reveals:
#   - How often he cuts inside from the right
#   - High-xG penalty box shots vs speculative long-range efforts
#   - 9 goals from 7.60 xG = genuine overperformance
MESSI = "Lionel Andrés Messi Cuccittini"
messi_shots = shots[shots["player"] == MESSI]
messi_goals = (messi_shots["outcome"] == "Goal").sum()
print(f"Messi shots: {len(messi_shots)} ({messi_goals} goals)")
print("Generating Messi shot map...")
fig1 = plot_shot_map(shots, player_name=MESSI, filename="04a_messi_shot_map.png")

# ── Map 2: Japan vs England pressure heatmap ──────────────────────────────────
# Japan (highest P/90 = 173) vs England (lowest P/90 = 97).
# Japan's heatmap should show more even/higher pressure across the pitch.
# England's should show pressure concentrated in specific zones (selective pressing).
print("Generating Japan pressure heatmap...")
fig2 = plot_pressure_heatmap(pressures, team_name="Japan", filename="04b_japan_pressure_heatmap.png")

print("Generating England pressure heatmap...")
fig3 = plot_pressure_heatmap(pressures, team_name="England", filename="04c_england_pressure_heatmap.png")

# ── Map 3: Morocco pressure heatmap ──────────────────────────────────────────
# Morocco was the tournament surprise — reached the semi-finals. Their pressing
# map (2nd highest P/90 = 155) is worth comparing to Japan's.
print("Generating Morocco pressure heatmap...")
fig4 = plot_pressure_heatmap(pressures, team_name="Morocco", filename="04d_morocco_pressure_heatmap.png")

print("\n" + "=" * 60)
print("Pitch Maps Generated")
print("=" * 60)
print("  04a_messi_shot_map.png         — Messi's 34 shots (bubble=xG, red=goal)")
print("  04b_japan_pressure_heatmap.png — Japan pressing zones (173 P/90)")
print("  04c_england_pressure_heatmap.png — England pressing zones (97 P/90)")
print("  04d_morocco_pressure_heatmap.png — Morocco pressing zones (155 P/90)")
print("\nReading the heatmaps:")
print("  Yellow/Red = high pressure density. Dark = few pressures.")
print("  A high-press team shows red in the opponent half (right side).")
print("  A low-block team shows concentration closer to their own goal.")
print("\n✓ Analysis 4 complete. All outputs saved to outputs/figures/")
