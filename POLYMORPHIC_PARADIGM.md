# Polymorphic Tournament Tracker - Architecture Documentation

## Overview

The Tournament Tracker has been refactored to follow a **polymorphic paradigm** where "everything accepts anything". This is a complete shift from traditional rigid type systems to a flexible, intelligent system that interprets intent rather than requiring specific formats.

## Core Philosophy

**"Accept anything, figure it out"**

Instead of:
```python
# Old way - rigid parameters
get_player_by_id(player_id: int)
get_players_by_name(name: str)
get_top_players(limit: int, event_type: str)
```

We now have:
```python
# New way - polymorphic
Player.find("west")           # Finds player named West
Player.find("top 8")          # Returns top 8 players
Player.find({"limit": 5})     # Returns top 5 players
Player.find(8)                # Could be ID or "top 8"
```

## Architecture Components

### 1. Discord Bridge (`discord_bridge.py`)
**Pure message forwarding - ZERO business logic**

```python
# Minimal 100-line bridge
class DiscordBridge:
    async def on_message(self, message):
        # Just forward to Claude service
        result = await process_message_async(message.content, context)
        await message.channel.send(result['response'])
```

Key principles:
- No database access
- No business logic
- No data transformation
- Just a thin communication layer

### 2. Claude CLI Service (`claude_cli_service.py`)
**Single entry point for all AI interactions**

```python
# Uses authenticated CLI, not API keys
claude_cli = ClaudeCLIService()
response = claude_cli.ask("show top players")
```

Features:
- Uses `claude` command from logged-in session
- Queue-based request processing
- Automatic code generation and execution
- No API keys needed (uses `claude /login`)

### 3. Unified Visualizer (`visualizer.py`)
**Single source of truth for ALL visualization**

```python
viz = UnifiedVisualizer()
viz.visualize(anything)  # Figures out best visualization
```

### 4. Database Models with On-The-Fly Calculations

**Important**: Data is calculated dynamically, not stored:

```python
# total_points is NOT a column - it's calculated via joins
query = session.query(
    Player,
    func.sum(
        case(*[(TournamentPlacement.placement == p, points) 
               for p, points in PLACEMENT_POINTS.items()], 
             else_=0)
    ).label('total_points')
).join(TournamentPlacement).group_by(Player.id)
```

## Key Paradigm Shifts

### 1. From Multiple Entry Points to Single Entry Point

**Before:**
```python
# Multiple modules, multiple functions
from player_utils import get_player_stats
from tournament_utils import fetch_tournaments
from discord_commands import handle_command
from api_client import make_request
```

**After:**
```python
# Single entry point
from go import TournamentCommand
cmd = TournamentCommand()
result = cmd.execute(anything)
```

### 2. From Rigid Types to Polymorphic Inputs

**Before:**
```python
def get_tournaments(start_date: datetime, end_date: datetime, 
                   venue_id: int, min_attendees: int):
    # Rigid parameter requirements
```

**After:**
```python
def find(input_data):
    # Accepts:
    # - "recent" -> recent tournaments
    # - {"year": 2025} -> tournaments in 2025
    # - "large" -> tournaments with many attendees
    # - datetime object -> tournaments on that date
    # - [lat, lng] -> tournaments near location
```

### 3. From Static Data to Dynamic Calculations

**Before:**
```python
class Player:
    total_points = Column(Integer)  # Stored in database
    win_rate = Column(Float)        # Stored in database
```

**After:**
```python
class Player:
    @property
    def total_points(self):
        # Calculated on-the-fly from placements
        return sum(placement.points for placement in self.placements)
    
    @property
    def win_rate(self):
        # Calculated when needed
        return self.first_places / self.total_events if self.total_events else 0
```

## Service Architecture

### Discord Integration Flow

```
Discord Message → Discord Bridge → Claude CLI Service → Database Query → Response
                      ↓                    ↓                   ↓
                 (No logic)         (Uses 'claude')    (Dynamic calc)
```

### Authentication Architecture

```
Traditional:  API Key → Anthropic API → Response
Our System:   claude /login → CLI Session → claude command → Response
```

Benefits:
- No API key management
- Uses existing authenticated session
- Same interface as terminal usage

## Implementation Patterns

### Polymorphic Method Pattern

```python
@accepts_anything
def find(cls, input_data):
    """Accept any input type and figure out intent"""
    
    # String input
    if isinstance(input_data, str):
        if input_data == "recent":
            return cls.get_recent()
        elif input_data.startswith("top"):
            limit = extract_number(input_data)
            return cls.get_top(limit)
        else:
            # Fuzzy search by name
            return cls.search_by_name(input_data)
    
    # Dictionary input
    elif isinstance(input_data, dict):
        return cls.filter(**input_data)
    
    # List input  
    elif isinstance(input_data, list):
        return [cls.find(item) for item in input_data]
    
    # Numeric input
    elif isinstance(input_data, (int, float)):
        return cls.get_by_id(input_data)
```

### Dynamic Calculation Pattern

```python
class Player:
    # No stored statistics columns
    
    def get_stats(self, session):
        """Calculate all stats on-the-fly"""
        return session.query(
            func.count(TournamentPlacement.id).label('events'),
            func.sum(case((TournamentPlacement.placement == 1, 1), 
                         else_=0)).label('wins'),
            func.sum(case(*[(TournamentPlacement.placement == p, points)
                          for p, points in POINTS.items()],
                         else_=0)).label('total_points')
        ).filter(
            TournamentPlacement.player_id == self.id
        ).first()
```

### Service Communication Pattern

```python
# Discord Bridge - Pure forwarding
async def on_message(message):
    result = await claude_service.process(message.content)
    await message.channel.send(result)

# Claude Service - Intelligent processing
def process(message):
    if is_database_query(message):
        code = generate_query_code(message)
        return execute_code(code)
    else:
        return ask_claude_directly(message)
```

## File Structure

```
tournament_tracker/
├── go.py                    # Single entry point for everything
├── tournament_tracker.py    # Main orchestrator
├── tournament_models.py     # Intelligent models with methods
├── database.py             # Single source for DB connections
├── discord_bridge.py       # Minimal Discord forwarding (100 lines)
├── claude_cli_service.py   # Claude CLI integration (no API keys)
├── visualizer.py           # Unified visualization (polymorphic)
├── fuzzy_search.py         # Fuzzy search utilities
└── startgg_sync.py        # Tournament synchronization
```

## Common Patterns & Examples

### Database Queries with Dynamic Calculations

```python
# Get top players with calculated points
from sqlalchemy import func, case, desc

PLACEMENT_POINTS = {1: 100, 2: 75, 3: 50, 4: 35, 5: 25, 6: 25, 7: 15, 8: 15}

query = session.query(
    Player,
    func.sum(
        case(*[(TournamentPlacement.placement == p, PLACEMENT_POINTS[p]) 
               for p in PLACEMENT_POINTS.keys()], 
             else_=0)
    ).label('total_points'),
    func.count(TournamentPlacement.id).label('tournament_count')
).join(TournamentPlacement)\
 .group_by(Player.id)\
 .order_by(desc('total_points'))\
 .limit(8)

results = query.all()
for player, points, events in results:
    print(f"{player.gamer_tag}: {points} points ({events} events)")
```

### Claude CLI Integration

```python
# Simple integration with authenticated CLI
import subprocess

def ask_claude(prompt):
    result = subprocess.run(
        ['claude'],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.stdout
```

### Polymorphic Visualization

```python
viz = UnifiedVisualizer()

# All these work
viz.visualize("Hello")                        # Text display
viz.visualize([1, 2, 3])                     # List chart
viz.visualize(tournaments)                    # Tournament heatmap
viz.visualize({"lat": 34.0, "lng": -118.0})  # Geographic point
viz.visualize(player_stats)                   # Player analytics
```

## Migration Guide

### Old Pattern → New Pattern

**Database Access:**
```python
# OLD: Multiple connection methods
conn = sqlite3.connect('tournament.db')
session = Session()
db = get_database()

# NEW: Single source
from database import session_scope
with session_scope() as session:
    # All database access here
```

**Discord Commands:**
```python
# OLD: Complex command handling
@bot.command()
async def top_players(ctx, limit: int = 8, event_type: str = "singles"):
    # Complex parameter parsing
    
# NEW: Natural language processing
async def on_message(message):
    # Just forward to Claude
    response = await ask_claude(message.content)
```

**Visualization:**
```python
# OLD: Multiple visualization modules
from heatmap_generator import create_heatmap
from chart_maker import make_chart
from html_formatter import format_html

# NEW: Single visualizer
from visualizer import UnifiedVisualizer
viz = UnifiedVisualizer()
viz.visualize(data)  # Figures out what to do
```

## Key Principles

1. **Everything is polymorphic** - Methods accept any input type
2. **Calculate on-the-fly** - No stored statistics, always fresh
3. **Single sources of truth** - One module per domain
4. **Thin bridges** - Service boundaries have no logic
5. **Natural language first** - Interpret intent, not syntax
6. **Queue everything** - Async processing with queues
7. **Use existing auth** - CLI session instead of API keys

## Testing

```python
# Test polymorphic inputs
test_inputs = [
    "top 8 players",
    {"limit": 5, "event": "singles"},
    ["player1", "player2"],
    datetime.now(),
    42
]

for input_data in test_inputs:
    result = Player.find(input_data)
    assert result is not None
```

## Troubleshooting

### Common Issues

1. **"total_points not found"**
   - Remember: total_points is calculated via joins, not a column
   - Use the full query pattern with TournamentPlacement joins

2. **Claude CLI timeout**
   - Check `claude --version` works
   - Ensure logged in with `claude /login`
   - Increase timeout if needed

3. **Discord not responding**
   - Check DISCORD_BOT_TOKEN in .env
   - Verify discord_bridge.py is running
   - Check logs for connection status

## Environment Setup

```bash
# Required environment variables
AUTH_KEY=<auth_key>                    # For system auth
DISCORD_BOT_TOKEN=<discord_token>      # Discord bot token
# ANTHROPIC_API_KEY is NOT needed - we use CLI

# Login to Claude CLI
claude /login  # One-time authentication

# Start services
./go.py --discord-bot  # Start Discord bridge
```

## Summary

The polymorphic paradigm represents a fundamental shift in how we build software:
- **From rigid to flexible**: Accept anything, interpret intent
- **From static to dynamic**: Calculate everything on-the-fly
- **From complex to simple**: Thin bridges, smart cores
- **From many to one**: Single sources of truth

This approach makes the system more maintainable, extensible, and user-friendly while reducing code complexity and duplication.