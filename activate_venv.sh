#!/bin/bash
# Activate the virtual environment for tournament_tracker

source /home/ubuntu/claude/tournament_tracker/venv/bin/activate
echo "Virtual environment activated. Python modules available:"
echo "- numpy"
echo "- sqlalchemy" 
echo "- alembic"
echo "- httpx"
echo "- flask"
echo "- discord.py"
echo ""
echo "To run tournament_tracker, use:"
echo "  python3 tournament_tracker.py"
echo "  or"
echo "  ./go.py"