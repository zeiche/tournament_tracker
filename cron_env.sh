#!/bin/bash
# Environment variables for cron jobs

# Load API keys from secure .env file
if [ -f "/home/ubuntu/claude/.env" ]; then
    source "/home/ubuntu/claude/.env"
else
    echo "Error: .env file not found" >&2
    exit 1
fi

# Additional tokens (keep these here as they're less sensitive)
export ACCESS_TOKEN='73546ba524cd5b68762731b9cc12cc46'
export DISCORD_BOT_TOKEN='YOUR_DISCORD_BOT_TOKEN_HERE'

# Python path
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PYTHONPATH="/home/ubuntu/claude/tournament_tracker:$PYTHONPATH"

# Working directory
export WORK_DIR="/home/ubuntu/claude/tournament_tracker"

# Log file
export CRON_LOG="/home/ubuntu/claude/tournament_tracker/cron.log"
