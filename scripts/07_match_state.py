"""
Script 07 — Match State Segmentation of Defensive Behaviour
=============================================================
Purpose: Examine whether teams press differently depending on the scoreline —
         a fundamental question about adaptive defensive behaviour.

Three match states are computed from the perspective of the pressing team:
  Winning  : pressing team leads at the time of each event
  Drawing  : scores are level
  Losing   : pressing team is behind

Research rationale:
  Game state is a major confounding variable in football analytics. A team that
  concedes early may press more desperately (chasing the game), while a team
  protecting a lead may drop into a defensive block and press less. If we measure
  pressing intensity WITHOUT accounting for game state, we mix two very different
  tactical situations.

  For a research paper, separating by match state allows you to ask:
  "Does pressing intensity increase when a team is losing?" (desperation press)
  or "Does winning change where a team presses?" (game management)

Implementation note:
  The score at each moment is reconstructed from shot events where outcome == "Goal",
  using vectorised cumsum — O(n) without row-by-row iteration. See src/metrics.py.

Run: python scripts/07_match_state.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import matplotlib.pyplot as plt
from src.data_loader import get_matches, get_all_events
from src.metrics import tag_match_state, pressure_zone_counts

FIGURES_DIR = Path(__file__).parent.parent / "outputs" / "figures"
TABLES_DIR = Path(__file__).parent.parent / "outputs" / "tables"

COMPETITION_ID = 43
SEASON_ID = 106

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading events (FIFA World Cup 2022, all 64 matches)...")
matches = get_matches(COMPETITION_ID, SEASON_ID)
match_ids = matches["match_id"].tolist()
events = get_all_events(match_ids)
print(f"  {len(events):,} events loaded.\n")

# ── Tag every event with the match state at that moment ───────────────────────
print("Tagging events with match state (reconstructing running score)...")
events_tagged = tag_match_state(events)
print(f"  Match state distribution:")
state_counts = events_tagged["match_state"].value_counts()
for state, count in state_counts.items():
    print(f"    {state:<10}: {count:>7,} events ({count / len(events_tagged) * 100:.1f}%)")

# ── Extract pressure events with state tags ────────────────────────────────────
pressures_tagged = events_tagged[events_tagged["type"] == "Pressure"].copy()
print(f"\n  Pressure events by state:")
press_state_counts = pressures_tagged["match_state"].value_counts()
for state, count in press_state_counts.items():
    print(f"    {state:<10}: {count:>6,} ({count / len(pressures_tagged) * 100:.1f}%)")

# ── Metric 1: Pressures per match by state ────────────────────────────────────
# Instead of per-90, we normalise by number of team-match-state exposures.
# A team playing 7 matches has more "Drawing time" than a team playing 3.
# We count how many distinct (team, match, state) combinations exist and
# divide total pressures by that count to get avg pressures per match-state.

state_summary = (
    pressures_tagged.groupby(["team", "match_state"])
    .agg(
        presses=("id", "count"),
        match_appearances=("match_id", "nunique"),
    )
    .reset_index()
)
state_summary["presses_per_match"] = (
    state_summary["presses"] / state_summary["match_appearances"]
).round(1)

# Pivot to wide format for easy reading
pivot = state_summary.pivot_table(
    index="team",
    columns="match_state",
    values="presses_per_match",
    aggfunc="first",
).fillna(0)

# Add a "Losing vs Winning" ratio: > 1 means team presses MORE when losing
for col in ["Winning", "Drawing", "Losing"]:
    if col not in pivot.columns:
        pivot[col] = 0

pivot["losing_vs_winning"] = (pivot["Losing"] / pivot["Winning"].replace(0, float("nan"))).round(2)
pivot = pivot.sort_values("losing_vs_winning", ascending=False)

print("\n" + "=" * 72)
print("Pressures per Match by Game State — FIFA World Cup 2022")
print("L/W ratio > 1 = team presses MORE when losing than winning")
print("=" * 72)
print(f"{'Team':<28} {'Winning':>8} {'Drawing':>8} {'Losing':>8} {'L/W Ratio':>10}")
print("-" * 72)
for team, row in pivot.iterrows():
    ratio_str = f"{row['losing_vs_winning']:.2f}" if not pd.isna(row["losing_vs_winning"]) else " N/A"
    print(
        f"{team:<28} {row['Winning']:>8.1f} {row['Drawing']:>8.1f} "
        f"{row['Losing']:>8.1f} {ratio_str:>10}"
    )

# ── Tournament-wide pattern ────────────────────────────────────────────────────
overall = (
    pressures_tagged.groupby("match_state")
    .agg(total=("id", "count"))
    .reset_index()
)
# Normalise by event count per state to account for more time spent drawing
events_per_state = events_tagged.groupby("match_state").size().reset_index(name="event_count")
overall = overall.merge(events_per_state, on="match_state")
overall["presses_per_1000_events"] = (overall["total"] / overall["event_count"] * 1000).round(1)
overall = overall.sort_values("presses_per_1000_events", ascending=False)

print("\n" + "=" * 55)
print("Tournament-Wide: Pressing Rate by Match State")
print("(presses per 1,000 events — controls for time exposure)")
print("=" * 55)
for _, r in overall.iterrows():
    bar = "█" * int(r["presses_per_1000_events"] / 4)
    print(f"  {r['match_state']:<10}: {r['presses_per_1000_events']:>5.1f}  {bar}")

# ── Metric 2: Pressing ZONE changes by match state ────────────────────────────
# Do teams press HIGHER UP the pitch when they're losing?
# (Desperation press: chase the ball in the opponent's half)
print("\n" + "=" * 60)
print("Pressing Zone by Match State (% in Attacking Third)")
print("=" * 60)
zone_by_state = {}
for state in ["Winning", "Drawing", "Losing"]:
    subset = pressures_tagged[pressures_tagged["match_state"] == state]
    zones = pressure_zone_counts(subset)
    att_pct = zones.loc[zones["zone"] == "Attacking Third", "pct"]
    att_pct_val = att_pct.values[0] if len(att_pct) > 0 else 0.0
    zone_by_state[state] = att_pct_val
    bar = "█" * int(att_pct_val / 1.5)
    print(f"  {state:<10}: {att_pct_val:>5.1f}% in attacking third  {bar}")

# ── Chart 1: Pressing by state — grouped bar chart ────────────────────────────
fig, ax = plt.subplots(figsize=(11, 8))

pivot_chart = pivot[["Winning", "Drawing", "Losing"]].copy()
pivot_chart_sorted = pivot_chart.sort_values("Drawing", ascending=True)

x = range(len(pivot_chart_sorted))
width = 0.25
colours = {"Winning": "#27ae60", "Drawing": "#f39c12", "Losing": "#e74c3c"}

for i, state in enumerate(["Winning", "Drawing", "Losing"]):
    ax.bar(
        [xi + (i - 1) * width for xi in x],
        pivot_chart_sorted[state],
        width=width, label=state,
        color=colours[state], alpha=0.85, edgecolor="white",
    )

ax.set_xticks(list(x))
ax.set_xticklabels(pivot_chart_sorted.index, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Pressures per match", fontsize=11)
ax.set_title(
    "Pressing Intensity by Match State — FIFA World Cup 2022\n"
    "Green = Winning | Orange = Drawing | Red = Losing",
    fontsize=12, fontweight="bold", pad=12
)
ax.legend(title="Match State", fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()

out_path = FIGURES_DIR / "07a_pressing_by_match_state.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"\nSaved: {out_path}")
plt.close(fig)

# ── Chart 2: Attacking-third press % by match state ──────────────────────────
fig2, ax2 = plt.subplots(figsize=(7, 4))
states = ["Winning", "Drawing", "Losing"]
vals = [zone_by_state[s] for s in states]
bar_colours = [colours[s] for s in states]

bars = ax2.bar(states, vals, color=bar_colours, alpha=0.85, edgecolor="white", width=0.5)
for bar, val in zip(bars, vals):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
             f"{val:.1f}%", ha="center", va="bottom", fontsize=11, fontweight="bold")

ax2.set_ylabel("% of pressures in attacking third", fontsize=11)
ax2.set_title(
    "Do Teams Press Higher When Losing?\nProportion of Pressures in Attacking Third by Match State",
    fontsize=11, fontweight="bold", pad=10
)
ax2.spines[["top", "right"]].set_visible(False)
ax2.set_ylim(0, max(vals) * 1.2)
fig2.tight_layout()

out_path2 = FIGURES_DIR / "07b_press_zone_by_state.png"
fig2.savefig(out_path2, dpi=150, bbox_inches="tight")
print(f"Saved: {out_path2}")
plt.close(fig2)

# ── Save table ────────────────────────────────────────────────────────────────
pivot.reset_index().to_csv(TABLES_DIR / "pressing_by_match_state.csv", index=False)
print(f"Saved: {TABLES_DIR / 'pressing_by_match_state.csv'}")

print("\n✓ Analysis 7 complete. Proceed to scripts/08_xg_conceded.py")
