# Tournament Tracker

A Python application for tracking and managing Fighting Game Community (FGC) tournaments in Southern California.

## Overview

This system synchronizes tournament data from start.gg, maintains a local SQLite database, and provides reporting functionality for tournament attendance and rankings.

## Quick Start

```bash
# Show statistics
./go.py --stats

# Sync tournaments from start.gg
./go.py --sync

# Generate console report
./go.py --console

# Generate HTML report
./go.py --html report.html

# Start interactive mode
./go.py --interactive
```

## Web Interfaces

### Database Editor (Port 8081)
Web-based interface for managing tournament organizations and fixing naming issues.

```bash
# Start the web editor
python3 web_editor.py

# Access via browser or lynx
lynx http://localhost:8081
```

**Features:**
- View tournaments with unnamed contacts (emails/Discord links)
- Map contacts to proper organization names
- View all organizations
- Edit tournament-organization associations

### Webhook Server (Port 8080)
Receives GitHub webhooks for automatic updates.

```bash
# Already running as systemd service
sudo systemctl status webhook-server

# Manual start if needed
python3 /home/ubuntu/webhook_server.py
```

## Project Structure

```
tournament_tracker/
├── go.py                    # Main CLI entry point
├── tournament_tracker.py    # Core application class
├── tournament_models.py     # SQLAlchemy database models
├── database_utils.py        # Database management utilities
├── startgg_sync.py         # start.gg API synchronization
├── tournament_report.py    # Report generation (HTML/console)
├── web_editor.py          # Web-based database editor
├── editor.py              # Legacy curses-based TUI editor
├── tournament_tracker.db  # SQLite database
└── alembic/              # Database migrations
```

## Current Issues

1. **Organization Naming**: Many tournaments are identified by contact info (email/Discord) instead of proper organization names
2. **Duplicates**: Some organizations appear multiple times in the database
3. **Data Quality**: Need to map contacts like "tryhardsbackyard@gmail.com" to "BACKYARD TRY-HARDS"

## Services

| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| webhook-server | 8080 | GitHub webhooks | Running (systemd) |
| web_editor | 8081 | Database management | Running (manual) |

## Database Management

### Using Web Interface
1. Open browser to http://localhost:8081
2. Click "View Unnamed Tournaments"
3. Edit each tournament to assign proper organization name
4. Use existing organizations or create new ones

### Using Interactive Mode
```bash
./go.py --interactive
# Python console with Tournament and Organization models loaded
```

### Direct Database Access
```bash
sqlite3 tournament_tracker.db
.tables  # Show all tables
.schema  # Show table structures
```

## Dependencies

- Python 3.12+
- SQLAlchemy
- httpx
- alembic
- requests

All dependencies installed via apt:
```bash
sudo apt install python3-sqlalchemy python3-httpx python3-alembic
```

## Logs

- Tournament tracker: `tournament_tracker.log`
- Webhook server: `/var/log/webhook-server.log`
- Web editor: `web_editor.log`

## Maintenance

### Restart Services
```bash
# Webhook server (systemd)
sudo systemctl restart webhook-server

# Web editor (manual)
pkill -f web_editor.py
python3 web_editor.py &
```

### Check Status
```bash
./go.py --stats  # Database statistics
ps aux | grep -E "webhook|web_editor"  # Running processes
```

## Attendance Rankings

Current standings (as of last sync):
- BACKYARD TRY-HARDS: #6 with 663 attendance

View live rankings at: https://backyardtryhards.com/pages/attendance

## Contributing

1. Test changes locally first
2. Use the webhook server for automatic deployment
3. Update CHANGELOG.md with significant changes
4. Keep organization names consistent with official tournament listings

## Contact

For issues with unnamed tournaments, use the web editor at http://localhost:8081 to fix organization mappings.