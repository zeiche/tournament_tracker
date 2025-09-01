# Tournament Tracker Architecture

## System Flow

```
start.gg API → startgg_sync.py → SQLite DB → Reports/Web UI
                                      ↓
                                Organizations
                                Tournaments
                                Standings
```

## Key Design Patterns

### 1. Database Session Management
- Centralized session management in `database_utils.py`
- Lazy loading pattern for database connections
- Queue-based batch operations for performance

### 2. Contact Normalization Problem
**Current Issue**: Organizations identified by contact info instead of names

```python
# Current (problematic)
primary_contact: "tryhardsbackyard@gmail.com"
primary_contact: "https://discord.gg/vwFG4Jxr3G"

# Desired
primary_contact: "BACKYARD TRY-HARDS"
primary_contact: "OneMustFall Gaming"
```

### 3. Data Models

**Tournament**
- id, name, slug
- primary_contact (THIS IS THE PROBLEM FIELD)
- normalized_contact
- num_attendees, venue_name, city
- start_date, end_date

**Organization**
- id, name
- contact_email, contact_discord
- (Needs to be linked to tournaments properly)

**Standings**
- tournament_id, placement
- gamer_tag, prefix

## Critical Files

### Core Logic
- `tournament_tracker.py` - Main application, session management
- `database_utils.py` - Database initialization, connection management
- `tournament_models.py` - SQLAlchemy ORM models

### Sync & Import
- `startgg_sync.py` - Fetches from start.gg API (THIS CREATES THE NAMING PROBLEM)
- `startgg_query.py` - GraphQL queries for start.gg

### UI/Editing
- `web_editor.py` - Web interface for fixing organization names (NEW)
- `editor.py` - Curses TUI (deprecated, doesn't work over SSH)

### Entry Points
- `go.py` - Main CLI interface
- `go_interactive.py` - Interactive Python console

## The Organization Naming Problem

### Root Cause
When `startgg_sync.py` imports tournaments, it uses the raw contact information as the "primary_contact" field instead of mapping to organization names.

### Current Workarounds
1. Manual editing via web interface (http://localhost:8081)
2. Direct database updates
3. Interactive mode corrections

### Proper Solution (TODO)
1. Create organization mapping table
2. Update sync to map contacts → organizations
3. Add validation to prevent future unnamed entries

## Database Schema Issues

### Missing Relationships
- No proper foreign key between tournaments and organizations
- Organizations tracked separately from tournament contacts
- Duplicates due to lack of unique constraints

### Normalization Problems
- primary_contact should be organization_id (foreign key)
- Need junction table for many-to-many relationships
- Contact info should be in organization table only

## API Integration

### start.gg GraphQL
- API key needed (check environment)
- Rate limiting considerations
- Queries in `startgg_query.py`

### Shopify Integration
- `shopify_query.py` - Merchandise data
- `shopify_publish.py` - Publishing tournament data

## Performance Considerations

### Database Queue
- `database_queue.py` implements batch operations
- Reduces database writes
- Improves sync performance

### Caching
- No caching layer currently
- Could cache start.gg responses
- Organization lookups are frequent

## Security Notes

### Web Interfaces
- `web_editor.py` - Bound to localhost only
- `webhook_server.py` - Exposed on port 8080
- No authentication currently (relies on network security)

### Sensitive Data
- API keys (start.gg, Shopify)
- Database contains PII (emails, Discord handles)
- No encryption at rest

## Common Operations

### Fix Organization Names
```python
# The problem: tournaments have email/discord as primary_contact
# Solution: Map these to proper organization names

# Example mapping needed:
"tryhardsbackyard@gmail.com" → "BACKYARD TRY-HARDS"
"onemustfallgaming@gmail.com" → "OneMustFall Gaming"
"pow.gaming.official@gmail.com" → "POW?! Gaming"
```

### Find Duplicates
```sql
SELECT primary_contact, COUNT(*) 
FROM tournament 
GROUP BY primary_contact 
HAVING COUNT(*) > 1;
```

## Testing

- `startgg_test.py` - Tests start.gg sync
- No comprehensive test suite
- Manual testing via `./go.py --console`

## Known Bugs

1. Organizations appear multiple times in rankings
2. Discord/email used instead of org names
3. No deduplication logic
4. editor.py crashes over SSH (curses issue)
5. Some tournaments have null attendance

## Quick Fixes Needed

1. Map all email/Discord contacts to proper org names
2. Deduplicate organizations table
3. Add unique constraints to prevent future duplicates
4. Update sync logic to use organization names