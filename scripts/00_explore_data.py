"""
Sanity-check the StatsBomb data load and inspect event structure
before running the main analyses.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.data_loader import get_competitions, get_matches, get_all_events, get_shots, get_pressures

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 120)

COMPETITION_ID = 43
SEASON_ID = 106

comps = get_competitions()
print("Competitions available:")
print(comps[["competition_name", "season_name", "competition_id", "season_id"]].to_string(index=False))

matches = get_matches(COMPETITION_ID, SEASON_ID)
print(f"\nTotal matches: {len(matches)}")
print(matches[["match_id", "home_team", "away_team", "home_score", "away_score", "match_date"]].head(10).to_string(index=False))

sample_match_ids = matches["match_id"].head(5).tolist()
print(f"\nLoading events from 5 matches: {sample_match_ids}")
events = get_all_events(sample_match_ids)
print(f"Total event rows: {len(events):,}")

print("\nEvent types:")
print(events["type"].value_counts().to_string())

shots = get_shots(events)
print(f"\nShots: {len(shots)}")
print("Columns:", list(shots.columns))
key_cols = [c for c in ["player", "team", "minute", "location", "statsbomb_xg", "outcome", "shot_technique", "shot_body_part"] if c in shots.columns]
print(shots[key_cols].head(5).to_string(index=False))

pressures = get_pressures(events)
print(f"\nPressure events: {len(pressures)}")
print(pressures[["player", "team", "minute", "location"]].head(5).to_string(index=False))

print(f"\nSummary — {len(sample_match_ids)} matches:")
print(f"  Events: {len(events):,}  |  Types: {events['type'].nunique()}  |  Shots: {len(shots)}  |  Pressures: {len(pressures)}")
print(f"  Players with shots: {shots['player'].nunique()}")
print(f"  xG range: {shots['statsbomb_xg'].min():.3f} – {shots['statsbomb_xg'].max():.3f}  avg {shots['statsbomb_xg'].mean():.3f}")
