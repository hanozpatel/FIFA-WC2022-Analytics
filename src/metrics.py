"""
Football metric calculations.

Functions here take a cleaned DataFrame and return an aggregated result.
They are pure functions (no side effects) so they are easy to test and reuse.
"""

import numpy as np
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


def press_success_rate(events: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the press success rate per team.

    A press is "successful" if the very next event in the match shows the pressing
    team in possession (possession_team changes to the pressing team). This is a
    conservative definition — it only captures immediate turnovers, not sequences
    where the press forced an error two actions later.

    StatsBomb's possession_team column tracks which team controls possession at each
    event. A change means the ball was won back.

    Returns a DataFrame sorted by success_rate_pct descending.
    """
    ev = events.sort_values(["match_id", "index"]).copy()

    # Shift possession_team within each match to get the NEXT event's possession owner
    ev["next_possession_team"] = ev.groupby("match_id")["possession_team"].shift(-1)

    presses = ev[ev["type"] == "Pressure"].copy()

    # Press is successful when the next event's possession_team equals the presser's team
    presses["successful"] = presses["team"] == presses["next_possession_team"]

    summary = (
        presses.groupby("team")
        .agg(
            total_presses=("id", "count"),
            successful_presses=("successful", "sum"),
        )
        .reset_index()
    )
    summary["success_rate_pct"] = (
        summary["successful_presses"] / summary["total_presses"] * 100
    ).round(1)

    return summary.sort_values("success_rate_pct", ascending=False).reset_index(drop=True)


def ppda_per_team(events: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate PPDA (Passes Allowed Per Defensive Action) per team.

    PPDA = opponent_passes / (pressures + interceptions + tackles)

    Lower PPDA = more aggressive pressing (fewer opponent passes per defensive action).
    Higher PPDA = less intense press, defending deeper.

    Defensive actions counted: Pressure events + Interception events +
    Duel events of type "Tackle".

    Note: This implementation uses all-pitch passes (not restricted to opponent's
    half) for simplicity. Academic PPDA variants sometimes restrict to the
    opposition's own half — see Fernandez & Bornn (2018) for the full formulation.
    """
    teams = sorted(events["team"].dropna().unique())
    rows = []

    for team in teams:
        team_match_ids = events.loc[events["team"] == team, "match_id"].unique()
        match_ev = events[events["match_id"].isin(team_match_ids)]

        team_ev = match_ev[match_ev["team"] == team]
        opp_ev = match_ev[match_ev["team"] != team]

        pressures = int((team_ev["type"] == "Pressure").sum())
        interceptions = int((team_ev["type"] == "Interception").sum())

        tackles = 0
        if "duel_type" in team_ev.columns:
            tackles = int(
                (
                    (team_ev["type"] == "Duel") &
                    (team_ev["duel_type"].astype(str).str.contains("Tackle", na=False))
                ).sum()
            )

        def_actions = pressures + interceptions + tackles
        opp_passes = int((opp_ev["type"] == "Pass").sum())
        ppda = round(opp_passes / def_actions, 2) if def_actions > 0 else None

        rows.append({
            "team": team,
            "matches": len(team_match_ids),
            "pressures": pressures,
            "interceptions": interceptions,
            "tackles": tackles,
            "defensive_actions": def_actions,
            "opponent_passes": opp_passes,
            "ppda": ppda,
        })

    return pd.DataFrame(rows).sort_values("ppda").reset_index(drop=True)


def tag_match_state(events: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'match_state' column to every event: "Winning", "Drawing", or "Losing"
    from the perspective of the team performing that action.

    Uses vectorised cumsum to reconstruct the running score from goal events
    (shot events where shot_outcome == "Goal") without iterating row-by-row.

    The score at the moment of each event is the cumulative goals BEFORE that event
    (shift(1) after cumsum, filled with 0 for the first event of each group).
    """
    ev = events.sort_values(["match_id", "index"]).copy()

    # Identify goal events (type == Shot AND the shot resulted in a Goal)
    goal_col = "shot_outcome" if "shot_outcome" in ev.columns else "outcome"
    ev["_is_goal"] = ((ev["type"] == "Shot") & (ev[goal_col] == "Goal")).astype(int)

    # Goals scored by the acting team BEFORE each event (within each match+team group)
    ev["_team_goals_before"] = (
        ev.groupby(["match_id", "team"])["_is_goal"]
        .transform(lambda s: s.cumsum().shift(1).fillna(0))
    )

    # Total goals in the match BEFORE each event (all teams combined)
    ev["_total_goals_before"] = (
        ev.groupby("match_id")["_is_goal"]
        .transform(lambda s: s.cumsum().shift(1).fillna(0))
    )

    # Opponent goals before this event = total - acting team's goals
    ev["_opp_goals_before"] = ev["_total_goals_before"] - ev["_team_goals_before"]

    # Classify match state
    conditions = [
        ev["_team_goals_before"] > ev["_opp_goals_before"],
        ev["_team_goals_before"] < ev["_opp_goals_before"],
    ]
    ev["match_state"] = np.select(conditions, ["Winning", "Losing"], default="Drawing")

    ev = ev.drop(columns=["_is_goal", "_team_goals_before", "_total_goals_before", "_opp_goals_before"])

    return ev


def xg_conceded_per_team(events: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate average xG per shot conceded, per team.

    For each shot event, the "conceding team" is the other team in that match.
    Aggregating by conceding team gives us how many shots they faced and the
    total (and average) xG of those shots — a measure of defensive shot quality
    allowed, independent of whether the shots went in.

    Returns a DataFrame with one row per team, sorted by avg_xg_per_shot_conceded.
    """
    shots = events[events["type"] == "Shot"].copy()

    xg_col = "statsbomb_xg" if "statsbomb_xg" in shots.columns else "shot_statsbomb_xg"
    shots = shots.dropna(subset=[xg_col])

    # Map each match to its two teams
    teams_per_match = (
        events.groupby("match_id")["team"]
        .apply(lambda x: list(x.dropna().unique()))
        .reset_index()
        .rename(columns={"team": "match_teams"})
    )
    shots = shots.merge(teams_per_match, on="match_id", how="left")

    # The conceding team is whoever in the match is NOT the shooting team
    shots["conceding_team"] = shots.apply(
        lambda r: next(
            (t for t in r["match_teams"] if t != r["team"]), None
        ),
        axis=1,
    )
    shots = shots.dropna(subset=["conceding_team"])

    conceded = (
        shots.groupby("conceding_team")
        .agg(
            shots_faced=("id", "count"),
            xg_conceded=(xg_col, "sum"),
        )
        .reset_index()
        .rename(columns={"conceding_team": "team"})
    )
    conceded["xg_conceded"] = conceded["xg_conceded"].round(2)
    conceded["avg_xg_per_shot_conceded"] = (
        conceded["xg_conceded"] / conceded["shots_faced"]
    ).round(4)

    return conceded.sort_values("avg_xg_per_shot_conceded").reset_index(drop=True)
