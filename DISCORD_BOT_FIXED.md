# Discord Bot - FIXED & SIMPLIFIED

## ✅ Current Status

The Discord bot has been completely refactored to be a **pure message conduit** with minimal dependencies.

## Architecture

```
Discord Message
      ↓
discord_service.py (minimal wrapper)
      ↓
message_handler.py (central logic)
      ↓
polymorphic_queries.py (database queries)
      ↓
Response back to Discord
```

## Key Files

### 1. **discord_service.py** (Primary)
- Minimal Discord wrapper
- NO complex dependencies
- Just receives messages and sends responses
- Loads polymorphic_queries if available
- Falls back to echo mode if queries unavailable

### 2. **message_handler.py** (NEW)
- Central message processing logic
- Works with ANY input source (Discord, CLI, web)
- Handles all message routing
- Built-in commands: ping, help, status
- Database query integration

### 3. **discord_bot_minimal.py** (Backup)
- Absolute minimal implementation
- Echo mode for testing
- No dependencies on other modules

### 4. **discord_bot_simple.py** (Alternative)
- Simple implementation with query support
- Direct polymorphic_queries integration

## Deprecated/Removed Files

All these have been renamed to .bak:
- discord_bridge.py.bak (old complex bridge)
- discord_conversational.py.bak
- discord_commands.py.bak
- discord_bot_wrapper.py.bak
- discord_command_registry.py.bak
- claude_cli_service.py dependencies removed

## Configuration

In `.env` file:
```
DISCORD_BOT_TOKEN=YOUR_TOKEN_HERE
```

**Note**: The current token in .env appears to be invalid or expired. You'll need a valid Discord bot token.

## Testing

### Test Message Handler (Works without Discord):
```bash
python3 message_handler.py
```

### Test Discord Bot:
```bash
# With go.py
./go.py --discord-bot

# Direct
python3 discord_service.py
```

## Commands

When the bot is running with a valid token, these commands work:

- `ping` - Check if bot is alive
- `help` - Show available commands
- `status` - Show bot and database status
- `show player west` - Show player info
- `show top 10 players` - Show rankings
- `recent tournaments` - Show recent events
- Any polymorphic query

## Token Issue

The Discord bot requires a valid token. The current token appears to be invalid. To fix:

1. Go to https://discord.com/developers/applications
2. Select your bot application
3. Go to Bot section
4. Reset Token
5. Copy new token
6. Update in .env file:
   ```
   DISCORD_BOT_TOKEN=NEW_TOKEN_HERE
   ```

## Benefits of New Architecture

1. **Minimal Dependencies** - Just Discord + optional queries
2. **Pure Conduit** - No business logic in Discord layer
3. **Testable** - Message handler works without Discord
4. **Maintainable** - Clear separation of concerns
5. **Fallback Mode** - Works even if queries fail

## Summary

The Discord bot is now a simple, pure message conduit as requested. All complex dependencies have been removed. The bot just:
1. Receives messages from Discord
2. Passes them to the message handler
3. Sends responses back

Total simplicity achieved!