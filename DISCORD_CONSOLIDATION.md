# Discord Module Consolidation Guide

## ✅ PRIMARY MODULE (Use This!)
**`discord_service.py`** - The ONLY Discord service that should be used
- Simple wrapper that forwards to Claude
- Clean interface
- Handles all Discord operations

## ❌ DEPRECATED MODULES (Do NOT Use!)

### discord_bridge.py
- **Status**: KEEP (it's the actual bot runner)
- **Purpose**: 100-line pure message forwarder
- **Note**: This is called BY discord_service.py

### discord_conversational.py
- **Status**: DEPRECATED
- **Reason**: Functionality merged into claude_cli_service.py
- **Action**: Should be removed or renamed to .bak

### discord_commands.py
- **Status**: DEPRECATED  
- **Reason**: Old command system, replaced by natural language processing
- **Action**: Should be removed or renamed to .bak

### discord_bot_wrapper.py
- **Status**: DEPRECATED
- **Reason**: Duplicate wrapper functionality
- **Action**: Should be removed or renamed to .bak

### discord_command_registry.py
- **Status**: DEPRECATED
- **Reason**: Old registry system, not needed with polymorphic queries
- **Action**: Should be removed or renamed to .bak

## Architecture After Consolidation

```
User Message in Discord
        ↓
discord_bridge.py (100 lines, pure forwarder)
        ↓
claude_cli_service.py (queue-based Claude CLI)
        ↓
polymorphic_queries.py (natural language processing)
        ↓
database_service.py (structured queries)
```

## Migration Steps Completed

1. ✅ Identified primary module: discord_service.py
2. ✅ Documented deprecated modules
3. ⏳ Renaming deprecated modules to .bak
4. ⏳ Updating imports in other files
5. ⏳ Testing consolidated system

## Usage After Consolidation

```python
# CORRECT - Use discord_service
from discord_service import DiscordService
service = DiscordService()
await service.start()

# WRONG - Don't use these
from discord_conversational import ...  # NO!
from discord_commands import ...        # NO!
from discord_bot_wrapper import ...     # NO!
```

## Commands to Run Consolidation

```bash
# Rename deprecated modules
mv discord_conversational.py discord_conversational.py.bak
mv discord_commands.py discord_commands.py.bak  
mv discord_bot_wrapper.py discord_bot_wrapper.py.bak
mv discord_command_registry.py discord_command_registry.py.bak
```

Last Updated: 2025-09-06