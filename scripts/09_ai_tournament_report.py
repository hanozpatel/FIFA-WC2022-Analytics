"""
Load computed metric tables and call the Claude API to generate
a multi-section tournament intelligence report saved as markdown.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

TABLES_DIR = Path(__file__).parent.parent / "outputs" / "tables"
REPORTS_DIR = Path(__file__).parent.parent / "outputs" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("=" * 60)
    print("ANTHROPIC_API_KEY not set.")
    print("=" * 60)
    print("\nTo run this script:")
    print("  1. Get a free API key at https://console.anthropic.com")
    print("  2. export ANTHROPIC_API_KEY='your-key-here'")
    print("  3. python scripts/09_ai_tournament_report.py")
    print("\nThe key is only used locally and never stored in the repo.")
    sys.exit(0)

import anthropic


def load_table(filename: str, required_cols: list[str] | None = None) -> pd.DataFrame | None:
    path = TABLES_DIR / filename
    if not path.exists():
        print(f"  WARNING: {filename} not found — run scripts 01-08 first.")
        return None
    df = pd.read_csv(path)
    if required_cols:
        df = df[[c for c in required_cols if c in df.columns]]
    return df

print("Loading metric tables...")
xg_players   = load_table("xg_per_player.csv",         ["player", "shots_taken", "xg", "goals", "xg_diff"])
ppda         = load_table("ppda_per_team.csv",          ["team", "matches", "defensive_actions", "opponent_passes", "ppda"])
press_rate   = load_table("press_success_rate.csv",     ["team", "total_presses", "successful_presses", "success_rate_pct", "pressures_p90"])
match_state  = load_table("pressing_by_match_state.csv",["team", "Winning", "Drawing", "Losing", "losing_vs_winning"])
xg_conceded  = load_table("xg_conceded_vs_pressing.csv",["team", "shots_faced", "xg_conceded", "avg_xg_per_shot_conceded", "att_third_pct", "ppda"])

missing = [t for t, df in [("xg_per_player", xg_players), ("ppda", ppda),
           ("press_success_rate", press_rate), ("match_state", match_state),
           ("xg_conceded", xg_conceded)] if df is None]
if missing:
    print(f"Missing tables: {missing}. Run scripts 01-08 before this script.")
    sys.exit(1)

print("  All tables loaded.\n")


def to_md(df: pd.DataFrame, n: int = 20) -> str:
    return df.head(n).to_markdown(index=False, floatfmt=".2f")

prompt = f"""You are a senior football analytics consultant producing a tournament intelligence
report for a professional audience. All data below is computed from StatsBomb event-level
data for the FIFA World Cup 2022 (64 matches, 32 teams).

Write a comprehensive markdown report. Use ## headers for each section. Be analytically
specific — cite numbers, name teams and players, and explain what the patterns mean
tactically. Avoid generic football clichés.

---

## DATA PROVIDED

### 1. xG Per Player (top 20 by cumulative xG)
{to_md(xg_players, 20)}

Columns: shots_taken, xg (expected goals), goals (actual), xg_diff (goals minus xG —
positive = overperformed, negative = underperformed)

### 2. PPDA Per Team (Passes Allowed Per Defensive Action — lower = more aggressive press)
{to_md(ppda.sort_values("ppda"), 32)}

### 3. Press Success Rate Per Team
{to_md(press_rate.sort_values("success_rate_pct", ascending=False), 32)}

Columns: total_presses, successful_presses (immediate turnover), success_rate_pct (%),
pressures_p90 (volume normalised to 90 minutes)

### 4. Pressing Volume by Match State (pressures per match per state)
{to_md(match_state.sort_values("losing_vs_winning", ascending=False), 32)}

Columns: Winning/Drawing/Losing = pressures per match in each state,
losing_vs_winning = ratio (>1 means team presses MORE when losing)

### 5. xG Conceded vs Pressing Metrics
{to_md(xg_conceded.sort_values("avg_xg_per_shot_conceded"), 32)}

Columns: shots_faced, xg_conceded (total), avg_xg_per_shot_conceded,
att_third_pct (% of team's pressures in the attacking third), ppda

Key statistical finding: PPDA vs avg_xg_per_shot_conceded correlation = -0.429 (p=0.014).
This means more aggressive pressers concede higher-quality shots — but face fewer shots
overall. Spain: 27 shots faced (fewest), 0.2226 avg xG/shot (highest). Tunisia: 30 shots,
0.0800 avg xG/shot.

---

## REPORT SECTIONS REQUIRED

Write each of the following sections in full. Each should be 150-250 words.

### 1. Executive Summary
A sharp, executive-level overview of the tournament's key analytical patterns.
What story do the numbers collectively tell about Qatar 2022?

### 2. Attacking Talent — Who Really Delivered?
Analyse the xG data. Who outperformed their chances (elite finishing or luck)?
Who underperformed despite creating quality? What does this say about the finalists?

### 3. The Pressing Hierarchy — Tactics vs Results
Compare PPDA, press success rate, and press volume. Which teams pressed intelligently
vs recklessly? Discuss the volume-quality tradeoff (correlation = -0.465 between
P/90 and success rate). Name specific contrasting teams.

### 4. How Teams Changed Behaviour Under Pressure
Use the match state data. Do teams press more when losing, or less? Which teams
showed the most dramatic tactical adaptation? What does Brazil's 0.08 L/W ratio reveal?

### 5. The Central Research Finding — Does Pressing High Reduce Shot Quality?
Explain the PPDA vs xG conceded finding (r = -0.429, p = 0.014). What does it mean
that Spain conceded the highest xG per shot but faced the fewest shots? Frame this
as a hypothesis for further research: is this a universal tradeoff or a Qatar-specific pattern?

### 6. Data-Driven Best XI
Select 11 players from the tournament using only the metrics available (xG, xg_diff,
pressures, success rates). Explain each selection with a specific number. Format as
a 4-3-3 or 4-2-3-1 with a brief justification for each position.

### 7. Limitations and Next Steps
Be honest about what a 64-match single-tournament sample can and cannot prove.
What additional data or analyses would strengthen these findings for a research paper?
"""


print("Calling Claude API (claude-sonnet-4-6)...")
print("Generating tournament intelligence report...\n")

client = anthropic.Anthropic(api_key=api_key)

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system=(
        "You are a senior football analytics consultant. Write precise, data-driven analysis. "
        "Always cite specific numbers from the data provided. Use markdown formatting."
    ),
    messages=[
        {"role": "user", "content": prompt}
    ],
)

report_text = response.content[0].text


timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
full_report = f"""# FIFA World Cup 2022 — Tournament Intelligence Report
*Generated by Claude {response.model} | {timestamp}*
*Data source: StatsBomb Open Data (64 matches, 32 teams)*

---

{report_text}

---

*This report was generated automatically by [scripts/09_ai_tournament_report.py](../../scripts/09_ai_tournament_report.py)
using the Anthropic Claude API applied to engineered metrics from StatsBomb Open Data.
All statistics were computed from event-level data using the analysis pipeline in this repository.*
"""


out_path = REPORTS_DIR / "tournament_intelligence_report.md"
out_path.write_text(full_report, encoding="utf-8")

print(f"Report saved: {out_path}")
print(f"  Model: {response.model}")
print(f"  Input tokens:  {response.usage.input_tokens:,}")
print(f"  Output tokens: {response.usage.output_tokens:,}")
print(f"\nOpen the report:")
print(f"  open '{out_path}'")
print("\n✓ Script 09 complete.")
