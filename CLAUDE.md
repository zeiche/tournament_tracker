# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tournament Tracker is a Python application for tracking and managing Fighting Game Community (FGC) tournaments in Southern California. It synchronizes data from start.gg, maintains a local SQLite database, and provides reporting functionality.

## Key Commands

### Running the Application
```bash
# Main entry point with full CLI options
./go.py [options]

# Common operations:
./go.py --sync                    # Sync tournaments from start.gg
./go.py --console                  # Show console report
./go.py --html report.html        # Generate HTML report
./go.py --fetch-standings          # Fetch top 8 standings for major tournaments
./go.py --interactive              # Run interactive mode
./go.py --edit-contacts            # Launch web editor for contact management
./go.py --stats                    # Show database statistics

# Service management:
./go.py --setup-services TOKEN     # Setup both web and Discord services
./go.py --setup-discord TOKEN      # Setup Discord bot only
./go.py --service-status           # Check service status
```

### Services

The system includes two persistent services that run automatically:

#### Web Editor Service
- **Port**: 8081
- **Access**: http://localhost:8081
- **Purpose**: Edit organization names and consolidate contacts
- **Management**:
  ```bash
  sudo systemctl status tournament-web   # Check status
  sudo systemctl restart tournament-web  # Restart
  sudo journalctl -u tournament-web -f   # View logs
  ```

#### Discord Bot Service
- **Name**: try-hard#8718
- **Purpose**: Natural language interface to tournament data
- **Commands**: Conversational - just ask questions like:
  - "show me the top 10 organizations"
  - "what are the tournament stats?"
  - "tell me about SoCal FGC"
- **Management**:
  ```bash
  sudo systemctl status discord-bot    # Check status
  sudo systemctl restart discord-bot   # Restart
  sudo journalctl -u discord-bot -f    # View logs
  ```

#### Service Setup
```bash
# Initial setup (run once)
./setup_services.sh setup-all YOUR_DISCORD_TOKEN

# Check all services
./setup_services.sh status

# Start/stop services
./setup_services.sh start-all
./setup_services.sh stop-all
```

### Testing
```bash
# Run start.gg sync tests
python3 startgg_test.py
```

### Database Management
```bash
# Web editor for managing contacts/organizations (preferred)
./go.py --edit-contacts
# Access at http://localhost:8081 with browser or lynx

# Database migrations (using Alembic)
alembic upgrade head
```

## Architecture

### Core Modules

- **tournament_tracker.py**: Main application class with centralized session management
- **go.py**: CLI entry point for the tournament tracker system
- **database_utils.py**: Database initialization and utility functions using SQLAlchemy (auto-initializes on first use)
- **tournament_models.py**: SQLAlchemy ORM models for tournaments, organizations, and standings
- **startgg_sync.py**: Start.gg API client and synchronization logic
- **tournament_operations.py**: Operation tracking for tournament management
- **tournament_report.py**: HTML and console report generation
- **database_queue.py**: Queue-based database operations for performance
- **log_utils.py**: Centralized logging system with context support
- **html_utils.py**: Shared HTML generation utilities for consistent UI
- **editor_core.py**: Core business logic for editing tournament contacts
- **editor_web.py**: Web interface for contact management (runs on port 8081)
- **shopify_query.py**: Shopify integration for merchandise data
- **shopify_publish.py**: Publishing tournament data to Shopify

### Service Modules (in parent directory)

- **discord_conversational.py**: Natural language Discord bot interface
- **discord_commands.py**: Discord command definitions for tournament data
- **setup_services.sh**: Service management script for systemd
- **.env.discord**: Discord bot token configuration

### Database

- SQLite database: `tournament_tracker.db`
- Uses SQLAlchemy ORM with Alembic for migrations
- Centralized session management with lazy loading
- Queue-based batch operations for performance

### External Dependencies

The project uses these Python libraries:
- sqlalchemy - ORM and database management
- alembic - Database migrations
- httpx - HTTP client for API calls
- discord.py - Discord bot framework
- curses - TUI interface (built-in)

Install with:
```bash
pip3 install --break-system-packages sqlalchemy alembic httpx discord.py
```

### API Integration

- Start.gg GraphQL API for tournament data
- Shopify API for merchandise integration
- API keys should be configured (check environment variables or config files)

## Development Tips

- The application uses centralized logging through `log_utils.py` - use `log_info()`, `log_debug()`, and `log_error()` for consistent logging
- Database operations go through `database_utils.py` - always use the centralized session management
- The database auto-initializes with absolute path when first accessed from any directory
- The queue system in `database_queue.py` batches database writes for performance
- Test files exist but no formal test framework is configured - use `startgg_test.py` for testing start.gg sync

## Data Flow

1. **Data Import**: start.gg API → `primaryContact` field used as initial organization name
2. **Data Cleanup**: Web editor (port 8081) → Edit `display_name` to proper organization names
3. **Data Access**: Discord bot or CLI → Shows edited display names

## Common Tasks

### Setting up a new environment
```bash
# Clone and setup
cd /home/ubuntu/claude/tournament_tracker

# Install dependencies
pip3 install --break-system-packages sqlalchemy alembic httpx discord.py

# Setup services with Discord token
./setup_services.sh setup-all YOUR_DISCORD_TOKEN

# Initial data sync
./go.py --sync

# Edit organization names
./go.py --edit-contacts
# Open browser to http://localhost:8081
```

### Daily operations
```bash
# Check service status
./go.py --service-status

# Sync new tournaments
./go.py --sync

# View top organizations
./go.py --console --limit 10

# Or ask the Discord bot naturally:
# "show me the top organizations"
```