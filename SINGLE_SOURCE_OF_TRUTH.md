# Single Source of Truth Implementation

This document describes the Single Source of Truth (SSOT) pattern implementations in the Tournament Tracker codebase.

## 1. Database Access - `database.py`

**THE ONLY DATABASE ENTRY POINT**

All database connections and sessions MUST go through `database.py`. No other module should create database connections.

### Key Principles:
- **ONE engine** - Created once in `database.py`
- **ONE session factory** - Created once in `database.py`  
- **ONE scoped session** - Managed by `database.py`
- **NO direct SQLAlchemy imports** elsewhere for connections

### Approved Methods:
```python
from database import (
    get_session,        # Get scoped session
    session_scope,      # Context manager with auto-commit
    fresh_session,      # Fresh session (bypasses cache)
    clear_session,      # Clear session cache
)
```

### What's Prohibited:
```python
# NEVER do this outside database.py:
engine = create_engine(...)  # ❌ NO!
Session = sessionmaker(...)  # ❌ NO!
```

### Usage Example:
```python
# CORRECT - Using database.py
from database import session_scope

with session_scope() as session:
    tournaments = session.query(Tournament).all()
```

---

## 2. Discord Bot Operations - `discord_service.py`

**THE ONLY DISCORD BOT ENTRY POINT**

All Discord bot operations MUST go through `discord_service.py`. This ensures one Discord client, consistent message handling, and centralized bot configuration.

### Key Principles:
- **ONE Discord client** - Created only in discord_service
- **ONE bot instance** - Singleton pattern
- **ONE message handler** - All messages routed through service
- **ONE configuration** - Centralized in DiscordConfig
- **NO direct discord.py usage** elsewhere

### Approved Methods:
```python
from discord_service import discord_service

# Start bot
discord_service.run_blocking()

# Check status
stats = discord_service.get_statistics()

# Change mode
from discord_service import BotMode
discord_service.config.mode = BotMode.CONVERSATIONAL
```

### What's Prohibited:
```python
# NEVER do this outside discord_service.py:
import discord                      # ❌ NO!
client = discord.Client(...)        # ❌ NO!
@client.event                        # ❌ NO!
```

### Bot Modes:
- **SIMPLE** - Basic greetings and responses
- **CONVERSATIONAL** - Tournament data queries  
- **CLAUDE_ENHANCED** - Claude-powered responses
- **HYBRID** - Mix of all modes

---

## 3. Claude/AI Conversations - `claude_service.py`

**THE ONLY CLAUDE API ENTRY POINT**

All Claude/AI interactions MUST go through `claude_service.py`. This ensures consistent API usage, tracking, and configuration.

### Key Principles:
- **ONE Claude service instance** - Singleton pattern
- **ONE API client** - Lazy loaded, reused
- **ONE configuration** - Centralized in ClaudeConfig
- **NO direct AI/Anthropic API calls** elsewhere

### Approved Methods:
```python
from claude_service import claude_service

# Single question
result = claude_service.ask_question("What is X?")

# Terminal chat
result = claude_service.start_terminal_chat()

# Web chat
result = claude_service.start_web_chat(port=8082)

# Check if enabled
if claude_service.is_enabled:
    # Use Claude features
```

### What's Prohibited:
```python
# NEVER do this outside claude_service.py:
from ai_service import get_ai_service  # ❌ NO!
ai = get_ai_service()                  # ❌ NO!
response = ai.get_response_sync(...)   # ❌ NO!
```

### Integration in `go.py`:
```python
# All AI operations in go.py use claude_service
def ask_ai(self, question: str):
    from claude_service import claude_service
    result = claude_service.ask_question(question)
    return CommandResult(result.success, result.response)
```

---

## 4. Shopify Publishing - `shopify_service.py`

**THE ONLY SHOPIFY API ENTRY POINT**

All Shopify operations MUST go through `shopify_service.py`. This ensures consistent API usage, rate limiting, and centralized configuration.

### Key Principles:
- **ONE Shopify client** - Single HTTP session with connection pooling
- **ONE API configuration** - Centralized credentials and settings
- **ONE publishing pipeline** - Consistent data formatting and publishing
- **NO direct Shopify API calls** elsewhere

### Approved Methods:
```python
from shopify_service import shopify_service

# Publish tournament rankings
result = shopify_service.publish_tournament_rankings(format=PublishFormat.HTML)

# List resources
resources = shopify_service.list_resources(ShopifyResource.PAGE)

# Get statistics
stats = shopify_service.get_statistics()
```

### What's Prohibited:
```python
# NEVER do this outside shopify_service.py:
import requests
requests.post(shopify_url, ...)     # ❌ NO!
import shopify                      # ❌ NO!
```

### Publishing Formats:
- **HTML** - Rich formatted content
- **JSON** - Structured data
- **MARKDOWN** - Simple formatted text
- **CSV** - Tabular data

---

## 5. Logging - `log_manager.py`

**THE ONLY LOGGING ENTRY POINT**

All logging should go through the centralized LogManager to ensure consistent formatting, levels, and output.

### Key Principles:
- **ONE LogManager instance** - Singleton pattern
- **ONE root logger** - All module loggers derive from it
- **ONE configuration** - Centralized log settings
- **NO direct logging.Logger creation** elsewhere

### Approved Methods:
```python
from log_manager import LogManager

logger = LogManager().get_logger('module_name')
logger.info("Message")
logger.error("Error occurred")
```

---

## 6. HTML Rendering - `html_renderer.py`

**THE ONLY HTML GENERATION ENTRY POINT**

All HTML generation should use HTMLRenderer for consistent theming and structure.

### Key Principles:
- **ONE renderer per theme** - Consistent styling
- **ONE component registry** - Reusable components
- **NO scattered HTML string building** elsewhere

### Approved Methods:
```python
from html_renderer import HTMLRenderer

renderer = HTMLRenderer(theme='dark')
html = (renderer
    .start_page("Title")
    .add_section("Section", content)
    .finish_page())
```

---

## 7. Benefits of SSOT Pattern

1. **Consistency** - All operations go through one place
2. **Maintainability** - Changes only need to be made once
3. **Debugging** - Single point to add logging/monitoring
4. **Testing** - Mock one service instead of many
5. **Configuration** - Centralized settings management
6. **Resource Management** - Prevents duplicate connections/instances
7. **Statistics** - Easy to track usage and performance

---

## 8. Enforcement Rules

### During Code Review:
- ✅ Check that database operations use `database.py`
- ✅ Check that Discord bot operations use `discord_service.py`
- ✅ Check that Claude operations use `claude_service.py`
- ✅ Check that Shopify operations use `shopify_service.py`
- ✅ Check that logging uses `log_manager.py`
- ✅ Reject any PR that creates duplicate entry points

### Runtime Checks:
- `database.py` has a singleton check to prevent multiple imports
- `discord_service.py` uses singleton pattern
- `claude_service.py` uses singleton pattern
- `shopify_service.py` uses singleton pattern
- `log_manager.py` uses singleton pattern

### Migration:
Use `migration_guide.py` to update old code:
```bash
python3 migration_guide.py --update
```

---

## Summary

The Tournament Tracker now follows strict Single Source of Truth principles:

- **Database**: `database.py` - ONLY place for DB connections
- **Discord Bot**: `discord_service.py` - ONLY place for Discord client
- **Claude/AI**: `claude_service.py` - ONLY place for Claude API
- **Shopify**: `shopify_service.py` - ONLY place for Shopify API
- **Logging**: `log_manager.py` - ONLY place for log configuration
- **HTML**: `html_renderer.py` - ONLY place for HTML generation

This architecture ensures consistency, prevents resource leaks, and makes the codebase much easier to maintain and debug.