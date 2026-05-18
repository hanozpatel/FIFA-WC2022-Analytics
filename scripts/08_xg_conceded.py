"""
Cross-reference pressing aggression (PPDA, attacking-third press %)
with average xG per shot conceded — testing whether pressing harder reduces shot quality allowed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from src.data_loader import get_matches, get_all_events, get_pressures
from src.metrics import xg_conceded_per_team, pressure_zone_counts

FIGURES_DIR = Path(__file__).parent.parent / "outputs" / "figures"
TABLES_DIR = Path(__file__).parent.parent / "outputs" / "tables"

COMPETITION_ID = 43
SEASON_ID = 106

print("Loading events (FIFA World Cup 2022, all 64 matches)...")
matches = get_matches(COMPETITION_ID, SEASON_ID)
match_ids = matches["match_id"].tolist()
events = get_all_events(match_ids)
pressures = get_pressures(events)
print(f"  {len(events):,} events ready.\n")

print("Computing xG conceded per team...")
xg_con = xg_conceded_per_team(events)

print("Computing attacking-third pressure % per team...")

pressures = pressures.copy()
pressures["x"] = pressures["location"].apply(
    lambda loc: loc[0] if isinstance(loc, list) else None
)
pressures = pressures.dropna(subset=["x"])

team_zone_rows = []
for team in pressures["team"].unique():
    team_p = pressures[pressures["team"] == team]
    zones = pressure_zone_counts(team_p)
    att_row = zones[zones["zone"] == "Attacking Third"]
    att_pct = att_row["pct"].values[0] if len(att_row) > 0 else 0.0
    team_zone_rows.append({"team": team, "att_third_pct": att_pct})

zone_df = pd.DataFrame(team_zone_rows)

ppda_path = TABLES_DIR / "ppda_per_team.csv"
ppda_df = pd.read_csv(ppda_path) if ppda_path.exists() else None

analysis = xg_con.merge(zone_df, on="team", how="inner")
if ppda_df is not None:
    analysis = analysis.merge(ppda_df[["team", "ppda"]], on="team", how="left")

print("\n" + "=" * 78)
print("xG Conceded vs Pressing Metrics — FIFA World Cup 2022")
print("=" * 78)
print(f"{'Team':<28} {'ShotsFaced':>11} {'xGConceded':>11} {'Avg xG/shot':>12} {'Att3rd%':>8} {'PPDA':>6}")
print("-" * 78)
for _, r in analysis.sort_values("avg_xg_per_shot_conceded").iterrows():
    ppda_str = f"{r['ppda']:.2f}" if ppda_df is not None and not pd.isna(r.get("ppda")) else "  N/A"
    print(
        f"{r['team']:<28} {int(r['shots_faced']):>11} {r['xg_conceded']:>11.2f} "
        f"{r['avg_xg_per_shot_conceded']:>12.4f} {r['att_third_pct']:>8.1f} {ppda_str:>6}"
    )

clean = analysis.dropna(subset=["att_third_pct", "avg_xg_per_shot_conceded"])
r_zone, p_zone = stats.pearsonr(clean["att_third_pct"], clean["avg_xg_per_shot_conceded"])
print(f"\nCorrelation: attacking-third press % vs avg xG conceded per shot")
print(f"  r = {r_zone:.3f}, p = {p_zone:.3f}", end="")
print(" (significant)" if p_zone < 0.05 else " (not significant at p<0.05)")

if ppda_df is not None:
    clean2 = analysis.dropna(subset=["ppda", "avg_xg_per_shot_conceded"])
    r_ppda, p_ppda = stats.pearsonr(clean2["ppda"], clean2["avg_xg_per_shot_conceded"])
    print(f"\nCorrelation: PPDA vs avg xG conceded per shot")
    print(f"  r = {r_ppda:.3f}, p = {p_ppda:.3f}", end="")
    print(" (significant)" if p_ppda < 0.05 else " (not significant at p<0.05)")


def _scatter_with_regression(ax, x, y, labels, xlabel, ylabel, title, colour):
    ax.scatter(x, y, s=70, color=colour, alpha=0.8, edgecolors="white", linewidths=0.5, zorder=3)

    slope, intercept, r, p, _ = stats.linregress(x, y)
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, slope * x_line + intercept, "--", color="#2c3e50", linewidth=1.2, alpha=0.7,
            label=f"r={r:.2f}, p={p:.2f}")

    for xi, yi, label in zip(x, y, labels):
        ax.annotate(label, xy=(xi, yi), xytext=(4, 3), textcoords="offset points",
                    fontsize=7, color="#2c3e50")

    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)


fig, ax = plt.subplots(figsize=(10, 7))
_scatter_with_regression(
    ax,
    x=clean["att_third_pct"],
    y=clean["avg_xg_per_shot_conceded"],
    labels=clean["team"],
    xlabel="% of pressures in attacking third (high press)",
    ylabel="Avg xG per shot conceded",
    title="Does Pressing Higher Reduce Shot Quality Allowed?\nFIFA World Cup 2022",
    colour="#1a78cf",
)
fig.tight_layout()
out1 = FIGURES_DIR / "08a_att_press_vs_xg_conceded.png"
fig.savefig(out1, dpi=150, bbox_inches="tight")
print(f"\nSaved: {out1}")
plt.close(fig)

if ppda_df is not None:
    fig2, ax2 = plt.subplots(figsize=(10, 7))
    _scatter_with_regression(
        ax2,
        x=clean2["ppda"],
        y=clean2["avg_xg_per_shot_conceded"],
        labels=clean2["team"],
        xlabel="PPDA (lower = more aggressive press)",
        ylabel="Avg xG per shot conceded",
        title="Does Better PPDA Mean Better Shot Quality Allowed?\nFIFA World Cup 2022",
        colour="#e74c3c",
    )
    fig2.tight_layout()
    out2 = FIGURES_DIR / "08b_ppda_vs_xg_conceded.png"
    fig2.savefig(out2, dpi=150, bbox_inches="tight")
    print(f"Saved: {out2}")
    plt.close(fig2)

analysis.to_csv(TABLES_DIR / "xg_conceded_vs_pressing.csv", index=False)
print(f"Saved: {TABLES_DIR / 'xg_conceded_vs_pressing.csv'}")
