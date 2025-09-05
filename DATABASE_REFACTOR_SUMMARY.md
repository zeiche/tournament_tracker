# Database Access Refactoring Summary

## Problem Identified
Multiple modules were creating their own database connections instead of using the central `database` module:
- `database_utils.py` - Creating its own engine and session
- `session_utils.py` - Also creating its own engine and session
- Various modules importing from these instead of the central `database` module

This violated the Single Source of Truth principle and could lead to:
- Multiple database connections
- Session conflicts
- Inconsistent connection parameters
- Difficult debugging

## Solution Implemented

### 1. Central Database Module
All database access should go through `/home/ubuntu/claude/tournament_tracker/database.py`:
```python
from database import session_scope, get_session, Session, engine, init_database
```

### 2. Compatibility Layers
Created compatibility shims for backward compatibility:
- `database_utils.py` now redirects to `database` module with deprecation warnings
- `session_utils.py` now redirects to `database` module with deprecation warnings

### 3. Modules Needing Updates
The following modules are currently using deprecated imports and should be updated:

#### High Priority (Core functionality):
- `startgg_sync.py` - Syncing tournaments from start.gg
- `discord_commands.py` - Discord bot commands
- `identify_organizations.py` - Organization identification
- `normalize_events.py` - Event normalization

#### Medium Priority (Analytics & Reports):
- `analytics_showcase.py`
- `heatmap_advanced.py`
- `relationship_demo.py`
- `database_debug.py`

#### Low Priority (Tests & Demos):
- `tests/*.py` - Test files
- `startgg_test.py`
- `debug.py`

## Migration Guide

### Old Way (DEPRECATED):
```python
from database_utils import get_session, init_db
from session_utils import Session, engine

# Using database_utils
init_db()
with get_session() as session:
    # database operations
```

### New Way (CORRECT):
```python
from database import session_scope, init_database

# Initialize once (usually in main)
init_database()

# Use session_scope for all database operations
with session_scope() as session:
    # database operations
```

## Benefits
1. **Single Database Connection** - Only one engine and session factory
2. **Centralized Configuration** - Database URL and settings in one place
3. **Better Error Handling** - Consistent session management
4. **Easier Debugging** - All database access goes through one module
5. **Thread Safety** - Scoped sessions managed properly

## Next Steps
1. Update all modules to import from `database` module directly
2. Remove deprecation warnings after transition period
3. Eventually remove compatibility shims
4. Add linting rules to prevent direct database access

## Testing
Run this to check for deprecation warnings:
```bash
python3 -c "from database_utils import get_session"
# Should show: DeprecationWarning: database_utils is deprecated...
```

Run this for the correct way:
```bash
python3 -c "from database import session_scope"
# Should work without warnings
```