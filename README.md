# Football Analytics Research — Practice Project

A structured practice environment for football (soccer) analytics, built toward a
research paper on **defensive behaviour and possession metrics**. This repository
uses the **StatsBomb Open Data** dataset and Python tooling to develop intuition
for event-level football data before applying the same techniques to proprietary data.

---

## Dataset

**StatsBomb Open Data — FIFA World Cup 2022**
- Source: [github.com/statsbomb/open-data](https://github.com/statsbomb/open-data)
- Access: Python SDK `statsbombpy` — no manual downloads required
- Competition: FIFA World Cup 2022 (`competition_id=43`, `season_id=106`)
- Coverage: All 64 matches, 32 teams, every player who featured
- Data type: Event-level (every pass, shot, pressure, tackle, dribble — with XY coordinates)
- Licence: StatsBomb Open Data Licence (non-commercial / research use permitted)
- Citation: StatsBomb Services Ltd. (2023). *StatsBomb Open Data* [Data set]. https://github.com/statsbomb/open-data

Alternative datasets available in the same SDK:
| Competition | IDs | Notes |
|---|---|---|
| UEFA Euro 2024 | `competition_id=55, season_id=282` | Most recent major tournament |
| 1. Bundesliga 2023/24 | `competition_id=9, season_id=281` | Most recent league season |
| Ligue 1 2022/23 | `competition_id=7, season_id=235` | 32 matches |

---

## Repository Structure

```
football-analytics/
├── data/
│   ├── raw/          # Raw data pulled from StatsBomb API (gitignored)
│   └── processed/    # Cleaned/aggregated data (gitignored)
├── notebooks/        # Exploratory Jupyter notebooks
├── scripts/          # Standalone analysis scripts (numbered by step)
├── src/              # Reusable Python modules
│   ├── data_loader.py    # StatsBomb loading + shot/pressure helpers
│   ├── metrics.py        # xG aggregation, pressures per 90, zone counts
│   └── viz.py            # Pitch maps and chart helpers (mplsoccer)
├── outputs/
│   ├── figures/      # Saved charts and pitch maps
│   └── tables/       # Saved CSV output tables
├── requirements.txt
└── README.md
```

---

## Setup

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd football-analytics

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run scripts in order
python scripts/00_explore_data.py
python scripts/01_xg_per_player.py
python scripts/02_xg_vs_goals.py
python scripts/03_defensive_metrics.py
python scripts/04_pitch_map.py
```

Note: The first run fetches data from GitHub via `statsbombpy` — subsequent runs
use a local cache and are significantly faster.

---

## Analyses Built

### Script 00 — Data Exploration ([scripts/00_explore_data.py](scripts/00_explore_data.py))
Loads the dataset, lists available competitions, inspects event types, and
prints a summary of shot and pressure event structures. Run this first to verify
your environment is working.

**Key finding:** 64 matches yield ~96,000 event rows; 1,494 shot events with
StatsBomb xG values ranging from 0.006 to 0.921 (avg 0.111 per shot).

---

### Script 01 — xG per Player ([scripts/01_xg_per_player.py](scripts/01_xg_per_player.py))
Aggregates StatsBomb's pre-computed xG per player, counting total shots, cumulative
xG, actual goals, and the over/underperformance difference (`xg_diff`).

**Output:** [outputs/tables/xg_per_player.csv](outputs/tables/xg_per_player.csv)

**Key findings (World Cup 2022):**
| Player | Shots | xG | Goals | xG Diff |
|--------|-------|----|-------|---------|
| Messi | 34 | 7.60 | 9 | +1.40 |
| Mbappé | 32 | 5.02 | 9 | **+3.98** |
| Lewandowski | 12 | 3.13 | 2 | -1.13 |
| Lautaro Martínez | 15 | 2.91 | 1 | -1.91 |
| Cristiano Ronaldo | 11 | 1.94 | 1 | -0.94 |

Mbappé's +3.98 xG diff over 32 shots is a statistically meaningful signal of
elite finishing. Lautaro's -1.91 over 15 shots reflects a genuine wasteful
tournament despite creating good chances for Argentina.

---

### Script 02 — xG vs Goals Visualisation ([scripts/02_xg_vs_goals.py](scripts/02_xg_vs_goals.py))
Produces two charts showing how actual goals compare to expected goals.

**Outputs:**
- [outputs/figures/01_xg_vs_goals_bar.png](outputs/figures/01_xg_vs_goals_bar.png) — side-by-side bar chart
- [outputs/figures/02_xg_vs_goals_scatter.png](outputs/figures/02_xg_vs_goals_scatter.png) — scatter plot with diagonal expectation line

**Reading the scatter:** Points above the diagonal line scored more than expected
(overperformers); below the line = underperformers. Bubble size encodes shots taken.

---

### Script 03 — Defensive Metrics ([scripts/03_defensive_metrics.py](scripts/03_defensive_metrics.py))
Calculates pressing intensity (pressures per 90) at player and team level, and
breaks down *where* on the pitch teams apply pressure (pitch thirds analysis).

**Outputs:**
- [outputs/figures/03_team_pressing_p90.png](outputs/figures/03_team_pressing_p90.png)
- [outputs/figures/03_pressure_zones_comparison.png](outputs/figures/03_pressure_zones_comparison.png)
- [outputs/tables/player_pressures_p90.csv](outputs/tables/player_pressures_p90.csv)
- [outputs/tables/team_pressures_p90.csv](outputs/tables/team_pressures_p90.csv)

**Key findings:**

| Team | P/90 |
|------|------|
| Japan | 173.0 (highest) |
| Morocco | 155.0 |
| England | 97.0 (lowest) |

Counterintuitive zone result: *bottom* pressers (England, Belgium, Portugal,
Switzerland) applied a higher share of their pressure in the attacking third
(28.2%) than top pressers (20.4%). Top pressers applied more in the defensive
third — suggesting reactive rather than proactive pressing when stretched.
This pattern directly informs our research question on defensive behaviour.

---

### Script 04 — Pitch Maps ([scripts/04_pitch_map.py](scripts/04_pitch_map.py))
Spatial visualisations placing event data directly on a football pitch using `mplsoccer`.

**Outputs:**
- [outputs/figures/04a_messi_shot_map.png](outputs/figures/04a_messi_shot_map.png) — Messi's 34 shots (bubble size = xG, red star = goal)
- [outputs/figures/04b_japan_pressure_heatmap.png](outputs/figures/04b_japan_pressure_heatmap.png) — Japan pressing density (173 P/90)
- [outputs/figures/04c_england_pressure_heatmap.png](outputs/figures/04c_england_pressure_heatmap.png) — England pressing density (97 P/90)
- [outputs/figures/04d_morocco_pressure_heatmap.png](outputs/figures/04d_morocco_pressure_heatmap.png) — Morocco pressing density (155 P/90)

---

## Research Direction

This practice work feeds into a research investigation of **defensive behaviour and
possession under pressure** — examining how teams structure defensive actions in
relation to possession transitions, and whether event-level pressure metrics predict
defensive outcomes better than traditional aggregated statistics.

**Natural next steps from this practice work:**
1. Link pressure events to the *possession* sequence that follows — does a successful
   press lead to a shot within the next N events?
2. Build a "PPDA" (Passes Allowed Per Defensive Action) metric, a standard pressing
   efficiency measure that combines pressures, tackles, and interceptions
3. Segment defensive actions by match state (winning/losing/drawing) to see if teams
   press differently under different scorelines
4. Cross-reference pressing zones with xG conceded in those zones — does pressing
   high actually reduce shot quality against you?

---

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `statsbombpy` | 1.18.0 | Load StatsBomb Open Data via Python API |
| `pandas` | 3.0.2 | Data manipulation and aggregation |
| `numpy` | 2.4.4 | Numerical computation |
| `matplotlib` | 3.10.9 | Base plotting |
| `mplsoccer` | 1.6.1 | Football pitch visualisations |
| `scipy` | 1.17.1 | Statistical analysis |
| `seaborn` | 0.13.2 | Statistical chart styling |

---

*Built with [Claude Code](https://claude.ai/code) as part of an academic football analytics research practice.*
