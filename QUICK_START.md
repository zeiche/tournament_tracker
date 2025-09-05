# Tournament Tracker - Quick Start Guide

## System Status Check

```bash
# Check if Discord bot is running
ps aux | grep discord_bridge

# Check Claude CLI
claude --version

# Check database
./go.py --stats
```

## Starting Services

### Discord Bot (Minimal Bridge)
```bash
# Start the Discord bridge
source /home/ubuntu/claude/.env && export DISCORD_BOT_TOKEN && python3 discord_bridge.py

# Or through go.py (if implemented)
./go.py --discord-bot
```

### Web Services
```bash
# Restart all web services
./go.py --restart-services

# Check service status
./go.py --service-status
```

## Discord Commands

The bot responds to natural language. Just type normally in Discord:

### Player Queries
- `show top 8 players` - Top players by points
- `show player monte` - Specific player stats
- `show player west` - Fuzzy search for players
- `top 5 players in singles` - Event-specific rankings

### Tournament Queries
- `recent tournaments` - Latest tournaments
- `upcoming tournaments` - Future events
- `large tournaments` - High attendance events
- `tournaments this month` - Time-based queries

### Statistics
- `show stats` - Database statistics
- `total players` - Player count
- `total tournaments` - Tournament count

### General Questions
- `What is the capital of France?` - Claude answers directly
- `How do I improve at fighting games?` - General advice

## Testing the System

### 1. Test Claude CLI Service
```python
python3 -c "
from claude_cli_service import ask_claude
response = ask_claude('show top 3 players')
print(response)
"
```

### 2. Test Database Queries
```python
python3 -c "
from database import session_scope
from tournament_models import Player
with session_scope() as session:
    players = session.query(Player).limit(5).all()
    for p in players:
        print(p.gamer_tag)
"
```

### 3. Test Discord Bridge
```python
python3 -c "
from discord_bridge import DiscordBridge
import asyncio

async def test():
    bridge = DiscordBridge()
    # Check if connected
    print(f'Bot ready: {bridge.client.user}')

asyncio.run(test())
"
```

## Common Operations

### Sync Tournaments from start.gg
```bash
./go.py --sync
```

### Generate Heat Maps
```bash
./go.py --heatmap
```

### View Console Report
```bash
./go.py --console
```

### Generate HTML Report
```bash
./go.py --html report.html
```

## Architecture Overview

```
User Message (Discord)
    ↓
discord_bridge.py (100 lines - NO logic)
    ↓
claude_cli_service.py (Uses 'claude' command)
    ↓
Database Query (Dynamic calculations)
    ↓
Response to Discord
```

## Key Files

| File | Purpose | Lines | Notes |
|------|---------|-------|-------|
| `discord_bridge.py` | Discord message forwarding | ~100 | Pure bridge, no logic |
| `claude_cli_service.py` | Claude CLI integration | ~400 | Queue-based, no API key |
| `tournament_models.py` | Database models | 2600+ | Intelligent models |
| `go.py` | Single entry point | ~1000 | All operations |
| `visualizer.py` | Unified visualization | ~500 | Polymorphic |

## Environment Variables

```bash
# Check current environment
cat /home/ubuntu/claude/.env

# Required variables:
AUTH_KEY=<key>                  # System auth
DISCORD_BOT_TOKEN=<token>       # Discord bot
# ANTHROPIC_API_KEY NOT NEEDED - using CLI
```

## Polymorphic Examples

Everything accepts anything:

```python
# All these work
Player.find("west")              # Name search
Player.find("top 8")             # Top players
Player.find({"wins": ">5"})      # Complex query
Player.find([1, 2, 3])           # Multiple IDs

Tournament.find("recent")        # Recent tournaments
Tournament.find("tuesday")       # Day-based search
Tournament.find({"year": 2025})  # Year filter
```

## Database Queries

Remember: Statistics are calculated on-the-fly, not stored!

```python
# Calculate player points (not stored as column)
from sqlalchemy import func, case, desc

PLACEMENT_POINTS = {1: 100, 2: 75, 3: 50, 4: 35, 5: 25}

query = session.query(
    Player,
    func.sum(
        case(*[(TournamentPlacement.placement == p, pts) 
               for p, pts in PLACEMENT_POINTS.items()], 
             else_=0)
    ).label('total_points')
).join(TournamentPlacement)\
 .group_by(Player.id)\
 .order_by(desc('total_points'))
```

## Debugging

### Enable Debug Logging
```python
# In claude_cli_service.py
logging.basicConfig(level=logging.DEBUG)
```

### Check Background Processes
```bash
# See all Python processes
ps aux | grep python3

# Check specific service
ps aux | grep discord_bridge
ps aux | grep claude_cli
```

### View Logs
```bash
# Tournament tracker logs
tail -f tournament_tracker.log

# Discord bridge output
# (Check the terminal where it's running)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Claude CLI timeout" | Check `claude --version`, re-login with `claude /login` |
| "total_points not found" | It's calculated via joins, not a column |
| Discord not responding | Check DISCORD_BOT_TOKEN, restart bridge |
| "No module named X" | Check imports, ensure in tournament_tracker directory |

## Quick Test Commands

```bash
# Test everything is working
./go.py --stats                 # Database stats
echo "2+2" | claude             # Claude CLI
python3 discord_bridge.py       # Discord bridge (Ctrl+C to stop)
```

## Support

- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Documentation: `/home/ubuntu/claude/tournament_tracker/POLYMORPHIC_PARADIGM.md`
- Main docs: `/home/ubuntu/claude/tournament_tracker/CLAUDE.md`