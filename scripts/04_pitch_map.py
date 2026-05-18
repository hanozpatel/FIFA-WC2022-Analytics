"""
Shot map for Messi and pressure density heatmaps for Japan, England,
and Morocco — rendered on a StatsBomb-scaled football pitch via mplsoccer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import get_matches, get_all_events, get_shots, get_pressures
from src.viz import plot_shot_map, plot_pressure_heatmap

COMPETITION_ID = 43
SEASON_ID = 106

print("Loading events (FIFA World Cup 2022, all 64 matches)...")
matches = get_matches(COMPETITION_ID, SEASON_ID)
match_ids = matches["match_id"].tolist()
events = get_all_events(match_ids)
shots = get_shots(events)
pressures = get_pressures(events)
print(f"  {len(shots)} shots, {len(pressures):,} pressures loaded.\n")

MESSI = "Lionel Andrés Messi Cuccittini"
messi_shots = shots[shots["player"] == MESSI]
messi_goals = (messi_shots["outcome"] == "Goal").sum()
print(f"Messi shots: {len(messi_shots)} ({messi_goals} goals)")
print("Generating Messi shot map...")
fig1 = plot_shot_map(shots, player_name=MESSI, filename="04a_messi_shot_map.png")

print("Generating Japan pressure heatmap...")
fig2 = plot_pressure_heatmap(pressures, team_name="Japan", filename="04b_japan_pressure_heatmap.png")

print("Generating England pressure heatmap...")
fig3 = plot_pressure_heatmap(pressures, team_name="England", filename="04c_england_pressure_heatmap.png")

print("Generating Morocco pressure heatmap...")
fig4 = plot_pressure_heatmap(pressures, team_name="Morocco", filename="04d_morocco_pressure_heatmap.png")
