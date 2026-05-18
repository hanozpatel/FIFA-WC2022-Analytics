# FIFA World Cup 2022 — Football Analytics

An end-to-end football analytics pipeline built on StatsBomb event-level data
from the **FIFA World Cup 2022** (Qatar, 64 matches, 32 teams). The project
computes attacking and defensive metrics from raw event data, visualises them
on pitch maps, runs statistical analyses, and synthesises findings into an
AI-generated tournament intelligence report using the **Claude API**.

Built as a research practice environment toward a paper on **defensive behaviour
and possession under pressure**.

---

## Dataset

**StatsBomb Open Data — FIFA World Cup 2022**

| Property | Value |
|---|---|
| Source | [github.com/statsbomb/open-data](https://github.com/statsbomb/open-data) |
| Access | `statsbombpy` Python SDK — no manual downloads |
| Scope | All 64 matches · 32 teams · every on-ball event with XY coordinates |
| Licence | StatsBomb Open Data Licence (non-commercial / research) |
| Citation | StatsBomb Services Ltd. (2023). *StatsBomb Open Data* [Data set]. https://github.com/statsbomb/open-data |

StatsBomb's event data includes a pre-computed xG value (`shot_statsbomb_xg`)
for every shot using their proprietary shot quality model — one of the most
accurate publicly available.

---

## Repository Structure

```
FIFA-WC2022-Analytics/
├── scripts/                      # Analysis pipeline — run in order (00 → 09)
│   ├── 00_explore_data.py        # Data loading, event type inspection, sanity checks
│   ├── 01_xg_per_player.py       # Cumulative xG per player + over/underperformance
│   ├── 02_xg_vs_goals.py         # xG vs actual goals — bar chart + scatter plot
│   ├── 03_defensive_metrics.py   # Pressures per 90 by player and team, pitch zones
│   ├── 04_pitch_map.py           # Shot map (Messi) + pressure heatmaps on pitch
│   ├── 05_press_outcomes.py      # Press success rate — volume vs effectiveness
│   ├── 06_ppda.py                # PPDA (Passes Allowed Per Defensive Action)
│   ├── 07_match_state.py         # Pressing by game state (winning / drawing / losing)
│   ├── 08_xg_conceded.py         # Pressing aggression vs shot quality allowed
│   └── 09_ai_tournament_report.py # Claude API: AI-generated tournament intelligence report
│
├── src/                          # Reusable Python modules
│   ├── data_loader.py            # StatsBomb loading helpers (competitions, matches, events)
│   ├── metrics.py                # All metric calculations (xG, PPDA, press rate, etc.)
│   └── viz.py                    # Pitch maps and charts via mplsoccer + matplotlib
│
├── outputs/
│   ├── figures/                  # PNG charts and pitch maps
│   ├── tables/                   # CSV metric tables
│   └── reports/                  # AI-generated markdown reports (not committed — requires API key)
│
├── data/
│   ├── raw/                      # StatsBomb raw cache (gitignored)
│   └── processed/                # Intermediate data (gitignored)
│
├── notebooks/                    # Jupyter notebooks for exploratory work
├── requirements.txt
├── run.sh                        # One-command pipeline runner (sets up venv + runs all scripts)
└── README.md
```

---

## Setup

```bash
git clone <your-repo-url>
cd FIFA-WC2022-Analytics
```

### Quick start (recommended)

`run.sh` handles everything — creates the virtual environment, installs dependencies, and runs the full pipeline in order:

```bash
./run.sh
```

To also generate the AI tournament report (script 09), set your Anthropic API key first:

```bash
export ANTHROPIC_API_KEY="your-key-here"   # get one at console.anthropic.com
./run.sh
```

> **First run note:** `statsbombpy` fetches data from GitHub on first use — this takes a few minutes. Subsequent runs use a local cache and are much faster.

### Manual setup

If you prefer to run scripts individually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/00_explore_data.py
python scripts/01_xg_per_player.py
python scripts/02_xg_vs_goals.py
python scripts/03_defensive_metrics.py
python scripts/04_pitch_map.py
python scripts/05_press_outcomes.py
python scripts/06_ppda.py
python scripts/07_match_state.py
python scripts/08_xg_conceded.py

# Optional — requires API key
export ANTHROPIC_API_KEY="your-key-here"
python scripts/09_ai_tournament_report.py
```

---

## Analysis Pipeline

### `00_explore_data.py` — Data Exploration
**What it does:** Loads the StatsBomb SDK, fetches all 64 World Cup 2022 matches,
loads events from a sample, and prints the full data structure — event types, column
names, shot details, pressure event samples.

**Run this first** to verify your environment and understand the raw data before
any analysis.

**Key output:**
```
Total events (64 matches): ~234,000 rows
Unique event types: 30
Shot events: 1,494  |  xG range: 0.006 – 0.921  |  avg 0.111/shot
Pressure events: 16,553
```

---

### `01_xg_per_player.py` — xG Per Player
**What it does:** Aggregates StatsBomb's pre-computed xG across all 64 matches to
produce a cumulative per-player table. Computes `xg_diff = goals − xG` to identify
finishers who over- or underperformed their chances.

**Output files:**
- `outputs/tables/xg_per_player.csv`

**Key results:**

| Player | Shots | xG | Goals | xG Diff |
|---|---|---|---|---|
| Messi | 34 | 7.60 | 9 | +1.40 |
| Mbappé | 32 | 5.02 | 9 | **+3.98** |
| Lewandowski | 12 | 3.13 | 2 | −1.13 |
| Lautaro Martínez | 15 | 2.91 | 1 | −1.91 |
| Cristiano Ronaldo | 11 | 1.94 | 1 | −0.94 |

Mbappé's +3.98 over 32 shots is a statistically meaningful overperformance signal.
Lautaro created quality chances but squandered them at scale.

---

### `02_xg_vs_goals.py` — xG vs Goals Visualisation
**What it does:** Produces two charts comparing expected goals to actual goals:
1. Horizontal bar chart — side-by-side xG vs goals for top players
2. Scatter plot — each dot is a player; the diagonal y=x line is "exact expectation";
   dots above the line are overperformers, below are underperformers; bubble size = shots.

**Output files:**
- `outputs/figures/01_xg_vs_goals_bar.png`
- `outputs/figures/02_xg_vs_goals_scatter.png`

---

### `03_defensive_metrics.py` — Pressures Per 90 + Pitch Zones
**What it does:** Calculates pressing intensity (pressures per 90 minutes) at both
player and team level. Also breaks down *where* on the pitch teams apply pressure —
defensive, middle, and attacking thirds.

**Output files:**
- `outputs/figures/03_team_pressing_p90.png`
- `outputs/figures/03_pressure_zones_comparison.png`
- `outputs/tables/player_pressures_p90.csv`
- `outputs/tables/team_pressures_p90.csv`

**Key results:**

| Team | P/90 |
|---|---|
| Japan | 173.0 — highest pressing volume |
| Morocco | 155.0 |
| England | 97.0 — lowest pressing volume |

Zone finding: the top 4 pressers apply 20.4% in the attacking third vs 28.2% for
the bottom 4 — high-volume pressers push deeper, not higher.

---

### `04_pitch_map.py` — Pitch Map Visualisations
**What it does:** Renders event data spatially on a football pitch using `mplsoccer`.
Produces Messi's full shot map (bubble = xG, red star = goal) and pressure density
heatmaps for Japan, England, and Morocco.

**Output files:**
- `outputs/figures/04a_messi_shot_map.png`
- `outputs/figures/04b_japan_pressure_heatmap.png`
- `outputs/figures/04c_england_pressure_heatmap.png`
- `outputs/figures/04d_morocco_pressure_heatmap.png`

---

### `05_press_outcomes.py` — Press Success Rate
**What it does:** Converts pressing from a volume metric into an *effectiveness* metric.
A press is "successful" if the very next event shows the pressing team in possession.
Plots volume vs success rate to reveal the quantity-vs-quality tradeoff.

**Output files:**
- `outputs/figures/05_press_volume_vs_success.png`
- `outputs/tables/press_success_rate.csv`

**Key finding:**
> Correlation between press volume (P/90) and success rate = **−0.465**
>
> Spain (111 P/90) → **18.0% success rate** (highest)
> Japan (173 P/90) → **5.8% success rate** (lowest)

---

### `06_ppda.py` — PPDA (Passes Allowed Per Defensive Action)
**What it does:** Computes the standard pressing efficiency metric. PPDA = opponent
passes ÷ (pressures + interceptions + tackles). Lower = more aggressive press.

**Output files:**
- `outputs/figures/06_ppda_per_team.png`
- `outputs/tables/ppda_per_team.csv`

**Key results:**

| Team | PPDA |
|---|---|
| Spain | **2.29** — most aggressive |
| Argentina | 2.88 |
| Japan | 3.94 |
| Poland | **4.63** — deepest block |

> Correlation between PPDA and press success rate = **−0.630** (strong positive link
> between pressing efficiency and turnover conversion).

---

### `07_match_state.py` — Pressing by Game State
**What it does:** Tags every event with the match state (Winning / Drawing / Losing)
at that moment by reconstructing the running score via vectorised cumsum. Analyses
how pressing volume and pitch zone shift with the scoreline.

**Output files:**
- `outputs/figures/07a_pressing_by_match_state.png`
- `outputs/figures/07b_press_zone_by_state.png`
- `outputs/tables/pressing_by_match_state.csv`

**Key findings:**

| State | Presses / 1,000 events | Attacking-third % |
|---|---|---|
| Winning | 75.0 (most) | 21.4% |
| Drawing | 70.4 | 24.2% |
| Losing | 66.7 (least) | **25.4%** (highest) |

Teams press *most by volume* when winning, but press *higher up the pitch* when losing.
Volume and zone are tactically independent signals. Brazil's L/W ratio = 0.08 (near-total
defensive block when behind). South Korea's = 14.50 (desperation high press).

---

### `08_xg_conceded.py` — Pressing Aggression vs Shot Quality Allowed
**What it does:** Cross-references pressing aggression (PPDA, attacking-third press %)
with average xG per shot conceded — testing whether pressing harder results in fewer
or lower-quality chances against.

**Output files:**
- `outputs/figures/08a_att_press_vs_xg_conceded.png`
- `outputs/figures/08b_ppda_vs_xg_conceded.png`
- `outputs/tables/xg_conceded_vs_pressing.csv`

**Central finding:**
> **PPDA vs avg xG per shot conceded: r = −0.429, p = 0.014 (statistically significant)**
>
> More aggressive pressers (lower PPDA) concede *higher-quality* shots per attempt
> — but face far *fewer* shots. Spain: 27 shots faced (fewest of any team), 0.2226
> avg xG/shot (highest). The tradeoff: **aggressive pressing reduces shot volume but
> the chances that break through are higher quality.** This is the empirical core
> finding bridging toward the research paper.

---

### `09_ai_tournament_report.py` — AI Tournament Intelligence Report
**What it does:** The pipeline's final stage. Loads all computed metric tables, sends
them to the **Claude API** (Anthropic) with a structured analyst prompt, and generates
a multi-section tournament intelligence report saved as markdown. Demonstrates the
complete data engineering pattern: raw events → engineered features → LLM synthesis
→ structured document.

**Requires:** An Anthropic API key.

```bash
export ANTHROPIC_API_KEY="your-key-here"
python scripts/09_ai_tournament_report.py
```

**Output files:**
- `outputs/reports/tournament_intelligence_report.md`

**Report sections Claude generates:**
1. Executive Summary
2. Attacking Talent — Who Really Delivered?
3. The Pressing Hierarchy — Tactics vs Results
4. How Teams Changed Behaviour Under Pressure
5. The Central Research Finding (pressing → shot quality tradeoff)
6. Data-Driven Best XI (metric-justified, position-by-position)
7. Limitations and Next Steps

---

## Key Findings Summary

| Finding | Value | Interpretation |
|---|---|---|
| Top xG overperformer | Mbappé +3.98 | Elite finishing signal |
| Top xG underperformer | Lautaro −1.91 | Wasteful with quality chances |
| Highest press volume | Japan 173 P/90 | High effort, low conversion |
| Highest press efficiency | Spain 18.0% success rate | Selective, lethal pressing |
| Most aggressive PPDA | Spain 2.29 | Fewest opponent passes allowed |
| Press volume vs success | r = −0.465 | More pressing ≠ better pressing |
| PPDA vs success rate | r = −0.630 | Efficient pressers win ball back more |
| Losing state behaviour | Zone shifts +4pp into att. third | Teams press higher, not harder |
| **Pressing vs xG conceded** | **r = −0.429, p = 0.014** | **Aggressive press → fewer but better-quality shots against** |

---

## Source Modules (`src/`)

| Module | Functions |
|---|---|
| `data_loader.py` | `get_competitions()` · `get_matches()` · `get_all_events()` · `get_shots()` · `get_pressures()` |
| `metrics.py` | `xg_per_player()` · `pressures_per_90()` · `pressure_zone_counts()` · `press_success_rate()` · `ppda_per_team()` · `tag_match_state()` · `xg_conceded_per_team()` |
| `viz.py` | `plot_xg_bar()` · `plot_shot_map()` · `plot_pressure_heatmap()` |

---

## Dependencies

| Library | Purpose |
|---|---|
| `statsbombpy` | StatsBomb Open Data Python SDK |
| `pandas` | Data manipulation and aggregation |
| `numpy` | Vectorised numerical computation |
| `matplotlib` | Base plotting |
| `mplsoccer` | Football pitch visualisations |
| `scipy` | Pearson correlation and statistical testing |
| `seaborn` | Statistical chart styling |
| `anthropic` | Claude API client for AI report generation |

---

## Research Direction

This project feeds into an investigation of **defensive behaviour and possession
under pressure** — specifically whether event-level pressing metrics (PPDA, press
success rate, pitch zone profiles) predict defensive outcomes (xG conceded) better
than traditional aggregated statistics.

The statistically significant finding from script 08 (r = −0.429, p = 0.014) is
the starting point: replicating this across full league seasons and controlling for
opposition quality would form the empirical core of the research paper.

---

*Data: StatsBomb Open Data · AI: Anthropic Claude API*
