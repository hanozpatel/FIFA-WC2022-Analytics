"""Football metric calculations on StatsBomb event data."""

import numpy as np
import pandas as pd


def xg_per_player(shots: pd.DataFrame) -> pd.DataFrame:
    """Aggregate xG and goal counts per player, sorted by cumulative xG."""
    shots = shots.copy()

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
    """Pressures per 90 minutes per player, using match count as proxy for minutes."""
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
        counts["est_minutes"] = counts["matches"] * 90
        counts["pressures_p90"] = (
            counts["total_pressures"] / counts["est_minutes"] * 90
        ).round(2)

    return counts.sort_values("pressures_p90", ascending=False).reset_index(drop=True)


def pressure_zone_counts(pressures: pd.DataFrame) -> pd.DataFrame:
    """Bin pressure events into defensive/middle/attacking thirds by x-coordinate."""
    pressures = pressures.copy()

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
    """Press success rate per team — fraction of pressures immediately winning possession."""
    ev = events.sort_values(["match_id", "index"]).copy()

    ev["next_possession_team"] = ev.groupby("match_id")["possession_team"].shift(-1)

    presses = ev[ev["type"] == "Pressure"].copy()

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
    """PPDA per team: opponent passes divided by (pressures + interceptions + tackles)."""
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
    """Add match_state column (Winning/Drawing/Losing) from each team's perspective using vectorised cumsum."""
    ev = events.sort_values(["match_id", "index"]).copy()

    goal_col = "shot_outcome" if "shot_outcome" in ev.columns else "outcome"
    ev["_is_goal"] = ((ev["type"] == "Shot") & (ev[goal_col] == "Goal")).astype(int)

    ev["_team_goals_before"] = (
        ev.groupby(["match_id", "team"])["_is_goal"]
        .transform(lambda s: s.cumsum().shift(1).fillna(0))
    )

    ev["_total_goals_before"] = (
        ev.groupby("match_id")["_is_goal"]
        .transform(lambda s: s.cumsum().shift(1).fillna(0))
    )

    ev["_opp_goals_before"] = ev["_total_goals_before"] - ev["_team_goals_before"]

    conditions = [
        ev["_team_goals_before"] > ev["_opp_goals_before"],
        ev["_team_goals_before"] < ev["_opp_goals_before"],
    ]
    ev["match_state"] = np.select(conditions, ["Winning", "Losing"], default="Drawing")

    ev = ev.drop(columns=["_is_goal", "_team_goals_before", "_total_goals_before", "_opp_goals_before"])

    return ev


def xg_conceded_per_team(events: pd.DataFrame) -> pd.DataFrame:
    """Average xG per shot conceded per team, identifying the conceding team per shot event."""
    shots = events[events["type"] == "Shot"].copy()

    xg_col = "statsbomb_xg" if "statsbomb_xg" in shots.columns else "shot_statsbomb_xg"
    shots = shots.dropna(subset=[xg_col])

    teams_per_match = (
        events.groupby("match_id")["team"]
        .apply(lambda x: list(x.dropna().unique()))
        .reset_index()
        .rename(columns={"team": "match_teams"})
    )
    shots = shots.merge(teams_per_match, on="match_id", how="left")

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
