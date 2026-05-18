#!/bin/bash
set -e

# Run from project root regardless of where the script is called from
cd "$(dirname "$0")"

# Need 3.10+ for union type hints in src/
python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null || {
    echo "Python 3.10 or higher is required."
    exit 1
}

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "=== FIFA World Cup 2022 Analytics Pipeline ==="
echo "Note: first run downloads data from StatsBomb GitHub — takes a few minutes."
echo ""

python scripts/00_explore_data.py
python scripts/01_xg_per_player.py
python scripts/02_xg_vs_goals.py
python scripts/03_defensive_metrics.py
python scripts/04_pitch_map.py
python scripts/05_press_outcomes.py
python scripts/06_ppda.py
python scripts/07_match_state.py
python scripts/08_xg_conceded.py

echo ""

# Script 09 calls the Claude API — skip gracefully if no key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Skipping script 09 (ANTHROPIC_API_KEY not set)."
    echo "To generate the AI tournament report:"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
    echo "  python scripts/09_ai_tournament_report.py"
else
    python scripts/09_ai_tournament_report.py
fi

echo ""
echo "Done. Outputs saved to outputs/"
