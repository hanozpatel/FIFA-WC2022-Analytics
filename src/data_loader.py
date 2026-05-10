"""
Utilities for loading StatsBomb Open Data.

StatsBomb organises data in three layers:
  competitions -> matches (within a competition+season) -> events (within a match)

We always load events, because that is the row-level data (one row per action).
"""

import pandas as pd
from statsbombpy import sb


def get_competitions() -> pd.DataFrame:
    """Return the full list of available competitions and seasons."""
    return sb.competitions()


def get_matches(competition_id: int, season_id: int) -> pd.DataFrame:
    """Return all matches for a given competition and season."""
    return sb.matches(competition_id=competition_id, season_id=season_id)


def get_all_events(match_ids: list[int]) -> pd.DataFrame:
    """
    Load and concatenate events for a list of match IDs.

    Each match produces ~2,000–4,000 event rows. Loading many matches at once
    can be slow the first time (data is fetched from GitHub), but statsbombpy
    caches responses locally.
    """
    frames = []
    for mid in match_ids:
        df = sb.events(match_id=mid)
        df["match_id"] = mid  # keep a reference back to the match
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def get_shots(events: pd.DataFrame) -> pd.DataFrame:
    """
    Filter events to shot events only.

    statsbombpy v1.x already flattens nested event attributes into prefixed
    columns (e.g. shot_statsbomb_xg, shot_outcome). We add convenience aliases
    so downstream code can use the shorter names.
    """
    shots = events[events["type"] == "Shot"].copy()

    # Add short-name aliases for the most-used shot columns
    if "shot_statsbomb_xg" in shots.columns and "statsbomb_xg" not in shots.columns:
        shots["statsbomb_xg"] = shots["shot_statsbomb_xg"]
    if "shot_outcome" in shots.columns and "outcome" not in shots.columns:
        shots["outcome"] = shots["shot_outcome"]

    return shots


def get_pressures(events: pd.DataFrame) -> pd.DataFrame:
    """Filter events to defensive pressure events."""
    return events[events["type"] == "Pressure"].copy()
