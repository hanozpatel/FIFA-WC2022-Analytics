"""Helpers for loading StatsBomb Open Data."""

import pandas as pd
from statsbombpy import sb


def get_competitions() -> pd.DataFrame:
    """Return the full list of available competitions and seasons."""
    return sb.competitions()


def get_matches(competition_id: int, season_id: int) -> pd.DataFrame:
    """Return all matches for a given competition and season."""
    return sb.matches(competition_id=competition_id, season_id=season_id)


def get_all_events(match_ids: list[int]) -> pd.DataFrame:
    """Load and concatenate events for a list of match IDs."""
    frames = []
    for mid in match_ids:
        df = sb.events(match_id=mid)
        df["match_id"] = mid  # keep a reference back to the match
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def get_shots(events: pd.DataFrame) -> pd.DataFrame:
    """Filter to shot events and add short-name aliases for statsbomb_xg and outcome."""
    shots = events[events["type"] == "Shot"].copy()

    if "shot_statsbomb_xg" in shots.columns and "statsbomb_xg" not in shots.columns:
        shots["statsbomb_xg"] = shots["shot_statsbomb_xg"]
    if "shot_outcome" in shots.columns and "outcome" not in shots.columns:
        shots["outcome"] = shots["shot_outcome"]

    return shots


def get_pressures(events: pd.DataFrame) -> pd.DataFrame:
    """Filter events to defensive pressure events."""
    return events[events["type"] == "Pressure"].copy()
