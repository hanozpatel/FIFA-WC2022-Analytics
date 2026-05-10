"""
Script 05 — Press Success Rate
================================
Purpose: Transform pressing from a volume metric into an *effectiveness* metric
         by measuring what fraction of presses immediately win the ball back.

Definition used here:
  A press is SUCCESSFUL if the very next event in the match shows the pressing
  team in possession (i.e. 'possession_team' flips to the pressing team).

Why "next event" and not longer chains?
  We could look 2, 3, or N events ahead, but each additional step introduces
  noise — was the turnover caused by the press, or by a mistake two passes later?
  "Immediate" turnovers are the most defensible measure for a practice dataset.
  Research papers (e.g. Andrienko et al., SIGKDD 2019) typically define
  press success within a bounded event window (3–10 events); we use 1 here
  for clarity, but the metric function can be extended.

Research connection:
  A high-volume, low-success press (e.g. many pressures but few turnovers) tells
  a very different story to a selective, high-success press. Distinguishing these
  is central to understanding defensive behaviour.

Run: python scripts/05_press_outcomes.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import matplotlib.pyplot as plt
from src.data_loader import get_matches, get_all_events, get_pressures
from src.metrics import press_success_rate

FIGURES_DIR = Path(__file__).parent.parent / "outputs" / "figures"
TABLES_DIR = Path(__file__).parent.parent / "outputs" / "tables"

COMPETITION_ID = 43
SEASON_ID = 106

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading events (FIFA World Cup 2022, all 64 matches)...")
matches = get_matches(COMPETITION_ID, SEASON_ID)
match_ids = matches["match_id"].tolist()
events = get_all_events(match_ids)
pressures = get_pressures(events)
print(f"  {len(pressures):,} pressure events ready.\n")

# ── Calculate press success rate ──────────────────────────────────────────────
success = press_success_rate(events)

# Also get volume (P/90) so we can cross-reference
volume = (
    pressures.groupby("team")
    .agg(
        total_presses=("id", "count"),
        matches=("match_id", "nunique"),
    )
    .reset_index()
)
volume["pressures_p90"] = (volume["total_presses"] / (volume["matches"] * 90) * 90).round(1)

# Merge volume into success table
combined = success.merge(volume[["team", "pressures_p90"]], on="team", how="left")

print("=" * 70)
print("Press Success Rate — FIFA World Cup 2022")
print("=" * 70)
print(f"{'Team':<28} {'Presses':>7} {'Won':>7} {'Rate %':>7} {'P/90':>6}")
print("-" * 70)
for _, r in combined.sort_values("success_rate_pct", ascending=False).iterrows():
    print(
        f"{r['team']:<28} {int(r['total_presses']):>7} "
        f"{int(r['successful_presses']):>7} {r['success_rate_pct']:>7.1f} "
        f"{r['pressures_p90']:>6.1f}"
    )

# ── Insight: does pressing more mean pressing better? ─────────────────────────
# If there's a negative correlation: high-volume teams win a lower % of presses
# (they're pressing indiscriminately). Positive correlation: efficient pressers
# are also high-volume. This directly informs tactical interpretation.
corr = combined["pressures_p90"].corr(combined["success_rate_pct"])
print(f"\nCorrelation (P/90 vs success rate): {corr:.3f}")
if corr < -0.3:
    print("  → High-volume teams tend to have LOWER success rates (quantity ≠ quality).")
elif corr > 0.3:
    print("  → High-volume teams also tend to have HIGHER success rates.")
else:
    print("  → No strong relationship between press volume and success rate.")

# ── Chart: Volume vs Success Rate scatter ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 7))

ax.scatter(
    combined["pressures_p90"],
    combined["success_rate_pct"],
    s=80, color="#1a78cf", alpha=0.8, edgecolors="white", linewidths=0.5, zorder=3
)

# Label every team
for _, r in combined.iterrows():
    ax.annotate(
        r["team"],
        xy=(r["pressures_p90"], r["success_rate_pct"]),
        xytext=(4, 3),
        textcoords="offset points",
        fontsize=7,
        color="#2c3e50",
    )

# Mean reference lines
ax.axvline(combined["pressures_p90"].mean(), color="#bdc3c7", linestyle="--", linewidth=1, alpha=0.8)
ax.axhline(combined["success_rate_pct"].mean(), color="#bdc3c7", linestyle="--", linewidth=1, alpha=0.8)

# Quadrant labels
ax.text(0.97, 0.97, "High volume\nHigh success", transform=ax.transAxes,
        ha="right", va="top", fontsize=8, color="#27ae60", alpha=0.7)
ax.text(0.03, 0.97, "Low volume\nHigh success", transform=ax.transAxes,
        ha="left", va="top", fontsize=8, color="#f39c12", alpha=0.7)
ax.text(0.97, 0.03, "High volume\nLow success", transform=ax.transAxes,
        ha="right", va="bottom", fontsize=8, color="#e74c3c", alpha=0.7)
ax.text(0.03, 0.03, "Low volume\nLow success", transform=ax.transAxes,
        ha="left", va="bottom", fontsize=8, color="#95a5a6", alpha=0.7)

ax.set_xlabel("Pressures per 90 minutes (volume)", fontsize=11)
ax.set_ylabel("Press success rate (%)", fontsize=11)
ax.set_title(
    "Press Volume vs Press Success Rate — FIFA World Cup 2022\n"
    f"Correlation: {corr:.2f}",
    fontsize=12, fontweight="bold", pad=12
)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()

out_path = FIGURES_DIR / "05_press_volume_vs_success.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"\nSaved: {out_path}")
plt.close(fig)

# ── Save table ────────────────────────────────────────────────────────────────
combined.sort_values("success_rate_pct", ascending=False).to_csv(
    TABLES_DIR / "press_success_rate.csv", index=False
)
print(f"Saved: {TABLES_DIR / 'press_success_rate.csv'}")

print("\n✓ Analysis 5 complete. Proceed to scripts/06_ppda.py")
