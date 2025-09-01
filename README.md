# Tournament Tracker

A Python application for tracking and managing Fighting Game Community (FGC) tournaments in Southern California. Features start.gg synchronization, web-based organization management, and a natural language Discord bot interface.

## Overview

This system synchronizes tournament data from start.gg, maintains a local SQLite database, provides reporting functionality for tournament attendance and rankings, and includes both web and Discord interfaces for data access.

## Quick Start

```bash
# Show statistics
./go.py --stats

# Sync tournaments from start.gg
./go.py --sync

# Generate console report
./go.py --console --limit 10

# Generate HTML report
./go.py --html report.html

# Start interactive mode
./go.py --interactive

# Setup services (one-time setup)
./setup_services.sh setup-all YOUR_DISCORD_TOKEN
```

## Services

The system includes two persistent services that automatically start on boot:

| Service | Port | Purpose | Access |
|---------|------|---------|--------|
| tournament-web | 8081 | Organization name editor | http://localhost:8081 |
| discord-bot | N/A | Natural language interface | Discord (try-hard#8718) |
| webhook-server | 8080 | GitHub webhooks | Internal only |

### Web Editor (Port 8081)

Web-based interface for managing tournament organizations and fixing naming issues.

```bash
# Service runs automatically, or start manually:
./go.py --edit-contacts

# Access via browser
http://localhost:8081
```

**Features:**
- View tournaments with unnamed contacts (emails/Discord links)
- Edit organization display names
- Consolidate duplicate organizations
- Map contacts to proper organization names

### Discord Bot

Natural language interface to tournament data. Just ask questions in plain English:

- "show me the top 10 organizations"
- "what are the tournament stats?"
- "tell me about SoCal FGC"
- "list organizations by attendance"

**Admin Commands:**
- `!sync` - Sync from start.gg (admin only)
- `!restart` - Restart bot (admin only)

### Service Management

```bash
# Check all services
./setup_services.sh status
./go.py --service-status

# Manage individual services
sudo systemctl status tournament-web
sudo systemctl status discord-bot
sudo systemctl restart tournament-web
sudo systemctl restart discord-bot

# View logs
sudo journalctl -u tournament-web -f
sudo journalctl -u discord-bot -f
```

## Project Structure

```
tournament_tracker/
├── go.py                      # Main CLI entry point
├── tournament_tracker.py      # Core application class
├── tournament_models.py       # SQLAlchemy database models
├── database_utils.py          # Database utilities (auto-initializes)
├── startgg_sync.py           # start.gg API synchronization
├── tournament_report.py      # Report generation
├── editor_web.py            # Web-based organization editor
├── tournament_tracker.db    # SQLite database
└── alembic/                # Database migrations

../
├── discord_conversational.py  # Natural language Discord bot
├── setup_services.sh         # Service management script
└── .env.discord             # Discord bot configuration
```

## Data Flow

1. **Import**: start.gg API → Tournaments imported with `primaryContact` as organization name
2. **Cleanup**: Web editor (8081) → Edit `display_name` to proper organization names
3. **Access**: Discord bot or CLI → Shows edited display names

## Database Management

### Using Web Interface (Recommended)
1. Open browser to http://localhost:8081
2. Click on organizations to edit their display names
3. Changes are saved immediately

### Using Interactive Mode
```bash
./go.py --interactive
# Python console with Tournament and Organization models loaded
```

### Direct Database Access
```bash
sqlite3 tournament_tracker/tournament_tracker.db
.tables  # Show all tables
.schema  # Show table structures
```

## Dependencies

```bash
# Install all dependencies
pip3 install --break-system-packages sqlalchemy alembic httpx discord.py

# Or individually via apt (partial support)
sudo apt install python3-sqlalchemy python3-httpx python3-alembic
```

## Common Tasks

### Initial Setup
```bash
# Clone repository
cd /home/ubuntu/claude/tournament_tracker

# Install dependencies
pip3 install --break-system-packages sqlalchemy alembic httpx discord.py

# Setup Discord bot (replace with your token)
./setup_services.sh setup-all YOUR_DISCORD_BOT_TOKEN

# Initial data sync
./go.py --sync

# Edit organization names
./go.py --edit-contacts
```

### Daily Operations
```bash
# Sync new tournaments
./go.py --sync

# Check statistics
./go.py --stats

# View rankings
./go.py --console --limit 20

# Or use Discord bot naturally
```

## Logs

- Tournament tracker: `tournament_tracker.log`
- Web editor: `editor_web.log`
- Discord bot: `discord_bot.log`
- Webhook server: `/var/log/webhook-server.log`

## Attendance Rankings

View live rankings:
- Console: `./go.py --console`
- Discord: Ask "show top organizations"
- Web: https://backyardtryhards.com/pages/attendance

## Troubleshooting

### Services not running
```bash
./setup_services.sh status
sudo systemctl restart tournament-web
sudo systemctl restart discord-bot
```

### Database issues
```bash
# Check database integrity
sqlite3 tournament_tracker.db "PRAGMA integrity_check;"

# Reset and resync
./go.py --sync
```

### Discord bot not responding
```bash
# Check logs
sudo journalctl -u discord-bot -n 50

# Verify token in .env.discord
cat /home/ubuntu/claude/.env.discord

# Restart
sudo systemctl restart discord-bot
```

## Contributing

1. Test changes locally first
2. Use the webhook server for automatic deployment
3. Keep organization names consistent with official tournament listings
4. Update documentation when adding features

## Contact

For issues with unnamed tournaments, use the web editor at http://localhost:8081 to fix organization mappings.