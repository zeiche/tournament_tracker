#!/bin/bash
# Cron job setup script for Tournament Tracker with Claude integration

# Set up environment variables for cron
# Cron jobs run with minimal environment, so we need to explicitly set variables

echo "Setting up cron environment for Tournament Tracker..."

# Create a cron environment file
cat > /home/ubuntu/claude/tournament_tracker/cron_env.sh << 'EOF'
#!/bin/bash
# Environment variables for cron jobs

# Load API keys from secure .env file
if [ -f "/home/ubuntu/claude/.env" ]; then
    source "/home/ubuntu/claude/.env"
else
    echo "Error: .env file not found" >&2
    exit 1
fi

# Additional tokens
export ACCESS_TOKEN='73546ba524cd5b68762731b9cc12cc46'

# Python path
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PYTHONPATH="/home/ubuntu/claude/tournament_tracker:$PYTHONPATH"

# Working directory
export WORK_DIR="/home/ubuntu/claude/tournament_tracker"

# Log file
export CRON_LOG="/home/ubuntu/claude/tournament_tracker/cron.log"
EOF

chmod +x /home/ubuntu/claude/tournament_tracker/cron_env.sh

# Create a wrapper script for cron jobs
cat > /home/ubuntu/claude/tournament_tracker/cron_wrapper.sh << 'EOF'
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
EOF

chmod +x /home/ubuntu/claude/tournament_tracker/cron_wrapper.sh

echo "Cron environment setup complete!"
echo ""
echo "Example crontab entries:"
echo ""
echo "# Sync tournaments daily at 2 AM"
echo "0 2 * * * /home/ubuntu/claude/tournament_tracker/cron_wrapper.sh /home/ubuntu/claude/tournament_tracker/go.py --sync"
echo ""
echo "# Generate reports weekly on Sunday at 3 AM"
echo "0 3 * * 0 /home/ubuntu/claude/tournament_tracker/cron_wrapper.sh /home/ubuntu/claude/tournament_tracker/go.py --html /home/ubuntu/claude/tournament_tracker/weekly_report.html"
echo ""
echo "# Check service status every hour"
echo "0 * * * * /home/ubuntu/claude/tournament_tracker/cron_wrapper.sh /home/ubuntu/claude/tournament_tracker/go.py --service-status"
echo ""
echo "To add these to your crontab, run: crontab -e"