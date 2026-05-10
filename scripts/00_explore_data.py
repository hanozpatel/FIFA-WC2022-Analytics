"""
Script 00 — Data Exploration
=============================
Purpose: Load StatsBomb Open Data, understand the structure, and confirm
         everything is working before running any analysis.

Competition choice: FIFA World Cup 2022 (Qatar) — Messi, Mbappé, Ronaldo,
the most-watched tournament of the last decade. 64 matches, rich event data,
results are intuitively checkable (we know who scored and who pressed well).
  - competition_id = 43  (FIFA World Cup)
  - season_id      = 106 (2022)

Alternative: UEFA Euro 2024 (competition_id=55, season_id=282) for the
             most recent major international tournament.

Run: python scripts/00_explore_data.py
"""

import sys
from pathlib import Path

# Make src/ importable from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.data_loader import get_competitions, get_matches, get_all_events, get_shots, get_pressures

pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 120)

# ── 1. Competitions available ────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Available competitions")
print("=" * 60)
comps = get_competitions()
print(comps[["competition_name", "season_name", "competition_id", "season_id"]].to_string(index=False))

# ── 2. Matches in FIFA World Cup 2022 ───────────────────────────────────────
COMPETITION_ID = 43   # FIFA World Cup
SEASON_ID = 106       # 2022

print("\n" + "=" * 60)
print(f"STEP 2: Matches in competition_id={COMPETITION_ID}, season_id={SEASON_ID}")
print("=" * 60)
matches = get_matches(COMPETITION_ID, SEASON_ID)
print(f"Total matches: {len(matches)}")
print(matches[["match_id", "home_team", "away_team", "home_score", "away_score", "match_date"]].head(10).to_string(index=False))

# ── 3. Load events from the first 5 matches (to keep it fast) ────────────────
print("\n" + "=" * 60)
print("STEP 3: Loading events from first 5 matches (sample)")
print("=" * 60)
sample_match_ids = matches["match_id"].head(5).tolist()
print(f"Match IDs: {sample_match_ids}")
events = get_all_events(sample_match_ids)
print(f"\nTotal event rows loaded: {len(events):,}")

# ── 4. Understand the event types ────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Event types (how StatsBomb categorises actions)")
print("=" * 60)
type_counts = events["type"].value_counts()
print(type_counts.to_string())

# ── 5. Examine shot events ────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: Shot events — structure and key columns")
print("=" * 60)
shots = get_shots(events)
print(f"Number of shots: {len(shots)}")
print("\nShot columns available:")
print(list(shots.columns))

# Show the most informative shot columns
key_cols = [c for c in ["player", "team", "minute", "location", "statsbomb_xg", "outcome", "shot_technique", "shot_body_part"] if c in shots.columns]
print(f"\nSample shot rows (key columns):")
print(shots[key_cols].head(5).to_string(index=False))

# ── 6. Examine pressure events ────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 6: Pressure events — defensive actions")
print("=" * 60)
pressures = get_pressures(events)
print(f"Number of pressure events: {len(pressures)}")
print("\nPressure columns:")
print(list(pressures.columns))
print(f"\nSample rows:")
print(pressures[["player", "team", "minute", "location"]].head(5).to_string(index=False))

# ── 7. Quick summary stats ────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 7: Quick summary")
print("=" * 60)
print(f"  Matches loaded          : {len(sample_match_ids)}")
print(f"  Total events            : {len(events):,}")
print(f"  Unique event types      : {events['type'].nunique()}")
print(f"  Shot events             : {len(shots)}")
print(f"  Pressure events         : {len(pressures)}")
print(f"  Players with shots      : {shots['player'].nunique()}")
print(f"  xG range (per shot)     : {shots['statsbomb_xg'].min():.3f} – {shots['statsbomb_xg'].max():.3f}")
print(f"  Avg xG per shot         : {shots['statsbomb_xg'].mean():.3f}")

print("\n✓ Data loaded and verified. Proceed to scripts/01_xg_per_player.py")
