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
- **database_utils.py**: Database initialization and utility functions using SQLAlchemy
- **tournament_models.py**: SQLAlchemy ORM models for tournaments, organizations, and standings
- **startgg_sync.py**: Start.gg API client and synchronization logic
- **tournament_operations.py**: Operation tracking for tournament management
- **tournament_report.py**: HTML and console report generation
- **database_queue.py**: Queue-based database operations for performance
- **log_utils.py**: Centralized logging system with context support
- **html_utils.py**: Shared HTML generation utilities for consistent UI
- **editor_core.py**: Core business logic for editing tournament contacts
- **editor_web.py**: Web interface for contact management (replaces old editor.py)
- **shopify_query.py**: Shopify integration for merchandise data
- **shopify_publish.py**: Publishing tournament data to Shopify

### Database

- SQLite database: `tournament_tracker.db`
- Uses SQLAlchemy ORM with Alembic for migrations
- Centralized session management with lazy loading
- Queue-based batch operations for performance

### External Dependencies

The project uses these Python libraries (no requirements.txt found, inferred from imports):
- sqlalchemy - ORM and database management
- alembic - Database migrations
- httpx - HTTP client for API calls
- curses - TUI interface (built-in)

### API Integration

- Start.gg GraphQL API for tournament data
- Shopify API for merchandise integration
- API keys should be configured (check environment variables or config files)

## Development Tips

- The application uses centralized logging through `log_utils.py` - use `log_info()`, `log_debug()`, and `log_error()` for consistent logging
- Database operations go through `database_utils.py` - always use the centralized session management
- The queue system in `database_queue.py` batches database writes for performance
- Test files exist but no formal test framework is configured - use `startgg_test.py` for testing start.gg sync