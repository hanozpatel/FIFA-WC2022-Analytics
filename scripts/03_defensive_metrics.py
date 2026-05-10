"""
Script 03 — Defensive Metrics
==============================
Purpose: Measure pressing intensity (pressures per 90) per player and per team,
         and show WHERE on the pitch teams apply pressure — a key indicator of
         defensive shape and tactical philosophy.

Key concepts:
  Pressure event: StatsBomb records a 'Pressure' whenever a player closes down
  an opponent in possession. It is the best proxy for pressing in event data.

  Pressures per 90: normalising by minutes prevents comparing a player who
  played 7 games to one who played 2. We use match count * 90 as a proxy since
  exact minutes-played data requires a separate extraction.

  Pitch thirds: The StatsBomb pitch is 120x80 yards.
    Defensive third   : x in [0, 40)
    Middle third      : x in [40, 80)
    Attacking third   : x in [80, 120]
  Pressure in the attacking third = high press. In the defensive third = low block.

Run: python scripts/03_defensive_metrics.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
from src.data_loader import get_matches, get_all_events, get_pressures
from src.metrics import pressures_per_90, pressure_zone_counts

TABLES_DIR = Path(__file__).parent.parent / "outputs" / "tables"
FIGURES_DIR = Path(__file__).parent.parent / "outputs" / "figures"
TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

COMPETITION_ID = 43   # FIFA World Cup
SEASON_ID = 106       # 2022

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading events (FIFA World Cup 2022, all 64 matches)...")
matches = get_matches(COMPETITION_ID, SEASON_ID)
match_ids = matches["match_id"].tolist()
events = get_all_events(match_ids)
pressures = get_pressures(events)
print(f"  {len(pressures):,} pressure events loaded across {len(match_ids)} matches.\n")

# ── Metric 1: Pressures per 90 per player ─────────────────────────────────────
# We only include players with at least 3 matches to filter out squad players
# who happened to press a lot in one appearance.
p90 = pressures_per_90(pressures)
p90_filtered = p90[p90["matches"] >= 3].copy()

print("=" * 65)
print("Top 20 Pressers — Pressures per 90 (min. 3 match appearances)")
print("=" * 65)
print(f"{'Player':<30} {'Matches':>7} {'Total':>7} {'P/90':>6}")
print("-" * 65)
for _, row in p90_filtered.head(20).iterrows():
    print(f"{row['player']:<30} {int(row['matches']):>7} {int(row['total_pressures']):>7} {row['pressures_p90']:>6.1f}")

# ── Metric 2: Team-level pressing ─────────────────────────────────────────────
# Aggregate total pressures by team across all matches, then normalise by
# the number of matches played (each match gives 90-min exposure per team).
team_matches = (
    pressures.groupby("team")["match_id"]
    .nunique()
    .reset_index()
    .rename(columns={"match_id": "matches_played"})
)
team_pressures = (
    pressures.groupby("team")
    .agg(total_pressures=("id", "count"))
    .reset_index()
    .merge(team_matches, on="team")
)
team_pressures["pressures_p90"] = (
    team_pressures["total_pressures"] / (team_pressures["matches_played"] * 90) * 90
).round(1)
team_pressures = team_pressures.sort_values("pressures_p90", ascending=False)

print("\n" + "=" * 55)
print("Team Pressing Intensity — Pressures per 90")
print("=" * 55)
print(f"{'Team':<28} {'Matches':>7} {'Total':>7} {'P/90':>6}")
print("-" * 55)
for _, row in team_pressures.iterrows():
    print(f"{row['team']:<28} {int(row['matches_played']):>7} {int(row['total_pressures']):>7} {row['pressures_p90']:>6.1f}")

# ── Metric 3: Pitch zone breakdown ────────────────────────────────────────────
# Where does pressing happen? Per team tells us their tactical shape.
# We pick the top 4 pressing teams vs. bottom 4 and compare zones.
top_teams = team_pressures.head(4)["team"].tolist()
bottom_teams = team_pressures.tail(4)["team"].tolist()

print("\n" + "=" * 55)
print("Pressure Zone Breakdown — Top 4 vs Bottom 4 Pressers")
print("=" * 55)
for label, teams in [("Top 4 pressing teams", top_teams), ("Bottom 4 pressing teams", bottom_teams)]:
    subset = pressures[pressures["team"].isin(teams)]
    zones = pressure_zone_counts(subset)
    print(f"\n  {label}:")
    for _, r in zones.iterrows():
        bar = "█" * int(r["pct"] / 2)
        print(f"    {str(r['zone']):<18} {int(r['pressure_count']):>5} ({r['pct']:>4.1f}%)  {bar}")

# ── Chart: Team pressing bar chart ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8))
sorted_teams = team_pressures.sort_values("pressures_p90")
colours = ["#e74c3c" if t in top_teams else "#3498db" for t in sorted_teams["team"]]
ax.barh(sorted_teams["team"], sorted_teams["pressures_p90"], color=colours, alpha=0.85, edgecolor="white")
ax.set_xlabel("Pressures per 90 minutes", fontsize=11)
ax.set_title("Team Pressing Intensity — FIFA World Cup 2022\nRed = top 4 pressers", fontsize=12, fontweight="bold", pad=12)
ax.axvline(team_pressures["pressures_p90"].mean(), color="#2c3e50", linestyle="--", linewidth=1.2, label=f"Mean: {team_pressures['pressures_p90'].mean():.1f}")
ax.legend(fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig_path = FIGURES_DIR / "03_team_pressing_p90.png"
fig.savefig(fig_path, dpi=150, bbox_inches="tight")
print(f"\nSaved: {fig_path}")
plt.close(fig)

# ── Chart: Zone stacked bar for top vs bottom pressers ────────────────────────
fig2, ax2 = plt.subplots(figsize=(8, 5))
zone_labels = ["Defensive Third", "Middle Third", "Attacking Third"]
colours_zones = ["#3498db", "#f39c12", "#e74c3c"]

for i, (label, teams) in enumerate([("Top 4 Pressers", top_teams), ("Bottom 4 Pressers", bottom_teams)]):
    subset = pressures[pressures["team"].isin(teams)]
    zones = pressure_zone_counts(subset).set_index("zone")["pct"]
    left = 0
    for zone, colour in zip(zone_labels, colours_zones):
        val = zones.get(zone, 0)
        ax2.barh(i, val, left=left, color=colour, label=zone if i == 0 else "", alpha=0.85, edgecolor="white")
        if val > 5:
            ax2.text(left + val / 2, i, f"{val:.0f}%", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
        left += val

ax2.set_yticks([0, 1])
ax2.set_yticklabels(["Top 4 Pressers", "Bottom 4 Pressers"], fontsize=11)
ax2.set_xlabel("% of all pressure events")
ax2.set_title("Where Do Teams Press? — Pitch Zone Breakdown\nFIFA World Cup 2022", fontsize=12, fontweight="bold", pad=10)
ax2.legend(loc="lower right", fontsize=9)
ax2.spines[["top", "right"]].set_visible(False)
fig2.tight_layout()
fig2_path = FIGURES_DIR / "03_pressure_zones_comparison.png"
fig2.savefig(fig2_path, dpi=150, bbox_inches="tight")
print(f"Saved: {fig2_path}")
plt.close(fig2)

# ── Save tables ────────────────────────────────────────────────────────────────
p90_filtered.to_csv(TABLES_DIR / "player_pressures_p90.csv", index=False)
team_pressures.to_csv(TABLES_DIR / "team_pressures_p90.csv", index=False)
print(f"Saved: {TABLES_DIR / 'player_pressures_p90.csv'}")
print(f"Saved: {TABLES_DIR / 'team_pressures_p90.csv'}")

print("\n✓ Analysis 3 complete. Proceed to scripts/04_pitch_map.py")
