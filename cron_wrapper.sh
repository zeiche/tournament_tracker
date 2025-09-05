#!/bin/bash
# Wrapper script for running tournament tracker commands via cron

# Source environment variables
source /home/ubuntu/claude/tournament_tracker/cron_env.sh

# Change to working directory
cd $WORK_DIR

# Log the execution
echo "$(date '+%Y-%m-%d %H:%M:%S') - Running: $@" >> $CRON_LOG

# Execute the command
"$@" >> $CRON_LOG 2>&1

# Log completion
echo "$(date '+%Y-%m-%d %H:%M:%S') - Completed: $@" >> $CRON_LOG
echo "----------------------------------------" >> $CRON_LOG
