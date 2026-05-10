"""
Football metric calculations.

Functions here take a cleaned DataFrame and return an aggregated result.
They are pure functions (no side effects) so they are easy to test and reuse.
"""

import pandas as pd


def xg_per_player(shots: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate xG and goal counts per player.

    StatsBomb includes 'statsbomb_xg' (their proprietary xG model value) on
    every shot row. We sum these to get cumulative xG, then compare to the
    actual number of shots that resulted in a goal.

    Returns a DataFrame sorted by xG descending.
    """
    # 'outcome' is a dict inside the shot column — after unpacking it becomes
    # a column called 'outcome' whose values are dicts with a 'name' key.
    # statsbombpy normalises this for us into an 'outcome' string column.
    shots = shots.copy()

    # outcome can be a dict {'id': ..., 'name': 'Goal'} or already a string
    if shots["outcome"].dtype == object and shots["outcome"].apply(
        lambda x: isinstance(x, dict)
    ).any():
        shots["outcome"] = shots["outcome"].apply(
            lambda x: x["name"] if isinstance(x, dict) else x
        )

    shots["is_goal"] = shots["outcome"] == "Goal"

    summary = (
        shots.groupby("player")
        .agg(
            shots_taken=("statsbomb_xg", "count"),
            xg=("statsbomb_xg", "sum"),
            goals=("is_goal", "sum"),
        )
        .reset_index()
    )

    summary["xg"] = summary["xg"].round(2)
    summary["xg_per_shot"] = (summary["xg"] / summary["shots_taken"]).round(3)
    summary["xg_diff"] = (summary["goals"] - summary["xg"]).round(2)

    return summary.sort_values("xg", ascending=False).reset_index(drop=True)


def pressures_per_90(pressures: pd.DataFrame, minutes_played: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Calculate pressures per 90 minutes per player.

    Without a minutes-played table we use a simpler proxy: count total pressures
    and normalise by the number of distinct matches the player appeared in,
    then scale to 90-minute equivalents assuming ~90 min/match.

    Args:
        pressures: DataFrame of pressure events (type == 'Pressure')
        minutes_played: Optional DataFrame with columns ['player', 'minutes'].
                        If None, match count proxy is used.

    Returns a DataFrame sorted by pressures_p90 descending.
    """
    counts = (
        pressures.groupby("player")
        .agg(
            total_pressures=("id", "count"),
            matches=("match_id", "nunique"),
        )
        .reset_index()
    )

    if minutes_played is not None:
        counts = counts.merge(minutes_played, on="player", how="left")
        counts["pressures_p90"] = (counts["total_pressures"] / counts["minutes"] * 90).round(2)
    else:
        # Proxy: assume 90 minutes per match appearance
        counts["est_minutes"] = counts["matches"] * 90
        counts["pressures_p90"] = (
            counts["total_pressures"] / counts["est_minutes"] * 90
        ).round(2)

    return counts.sort_values("pressures_p90", ascending=False).reset_index(drop=True)


def pressure_zone_counts(pressures: pd.DataFrame) -> pd.DataFrame:
    """
    Bin pressure events into thirds of the pitch by x-coordinate.

    StatsBomb uses a 120x80 yard pitch coordinate system.
    Defensive third: x in [0, 40), Mid third: [40, 80), Attacking third: [80, 120].
    """
    pressures = pressures.copy()

    # location is a list [x, y]; unpack it
    pressures["x"] = pressures["location"].apply(lambda loc: loc[0] if isinstance(loc, list) else None)

    bins = [0, 40, 80, 120]
    labels = ["Defensive Third", "Middle Third", "Attacking Third"]
    pressures["zone"] = pd.cut(pressures["x"], bins=bins, labels=labels, right=False)

    zone_counts = (
        pressures.groupby("zone", observed=True)
        .agg(pressure_count=("id", "count"))
        .reset_index()
    )
    zone_counts["pct"] = (zone_counts["pressure_count"] / zone_counts["pressure_count"].sum() * 100).round(1)

    return zone_counts
