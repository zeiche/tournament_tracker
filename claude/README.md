# Claude - AI Assistant with Bonjour Discovery

Claude is the AI assistant for the tournament tracker, enhanced with dynamic service discovery through Bonjour announcements.

## Directory Structure

```
claude/
├── services/           # Core Claude implementations
│   ├── claude_service.py           # Original static Claude service
│   └── claude_bonjour_service.py   # Enhanced with Bonjour discovery
├── bridges/            # Bridges to other systems
│   └── discord_claude_bridge.py    # Discord-Claude integration
├── utils/              # Claude utilities
│   └── conversation_manager.py     # Conversation context management
└── tests/              # Claude-specific tests
    ├── test_claude_bonjour.py      # Test discovery capabilities
    └── compare_claude_services.py  # Compare old vs new
```

## Key Features

### 1. Dynamic Service Discovery
Claude discovers services through Bonjour announcements instead of hardcoded knowledge:
- Services announce their capabilities
- Claude learns what's available at runtime
- Capabilities change as services start/stop

### 2. Natural Language Routing
Claude routes requests to appropriate services based on:
- Pattern matching from announcements
- Natural language understanding
- Service capability descriptions

### 3. Self-Assembling Conversations
- Claude's abilities grow as new services announce themselves
- No code changes needed when adding new services
- Services can have conversations through Claude

## Usage

### Basic Usage
```python
from claude import ask_claude_with_discovery

# Claude will use discovered services to answer
response = ask_claude_with_discovery("Show me top players")
```

### Check Capabilities
```python
from claude import get_claude_capabilities

# See what Claude can currently do
caps = get_claude_capabilities()
print(f"Services: {caps['discovered_services']}")
print(f"Active: {caps['active_services']}")
```

### Discord Integration
```python
from claude.bridges.discord_claude_bridge import ask_claude_from_discord

# Process Discord message with discovery context
response = await ask_claude_from_discord("What tournaments are coming up?")
```

## Service Integration

For a service to be discovered by Claude:

1. **Import announcer**:
```python
from polymorphic_core import announcer
```

2. **Announce capabilities**:
```python
announcer.announce(
    "Your Service Name",
    [
        "What your service can do",
        "Another capability",
        "Natural language descriptions"
    ],
    [
        "example.ask('query')",
        "example.do('action')"
    ]
)
```

3. **Claude automatically discovers it!**

## Migration from Old Claude

### Old Way (Static)
```python
# Fixed methods, must update for new features
result = claude_service.ask_about_tournaments(question)
result = claude_service.ask_about_players(question)
```

### New Way (Dynamic)
```python
# One method, discovers all capabilities
result = claude_bonjour.ask_with_discovery(question)
```

## Environment Variables

- `ANTHROPIC_API_KEY` - Required for Claude API access
- Set in `.env` file at project root

## Testing

Run tests from the project root:
```bash
# Test discovery capabilities
python3 claude/tests/test_claude_bonjour.py

# Compare old vs new
python3 claude/tests/compare_claude_services.py
```

## Architecture Benefits

1. **Zero Configuration Updates** - New services work immediately
2. **Real-Time Adaptation** - Claude knows what's currently running
3. **Natural Conversation Flow** - Services speak natural language
4. **Discoverability** - Ask Claude "what can you do?"
5. **Resilience** - Handles service failures gracefully

## Future Enhancements

- [ ] Service health monitoring
- [ ] Conversation persistence
- [ ] Multi-turn service orchestration
- [ ] Learning from usage patterns
- [ ] Service recommendation engine