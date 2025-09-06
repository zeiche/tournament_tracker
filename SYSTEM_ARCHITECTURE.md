# Tournament Tracker System Architecture

## Core Philosophy: Everything Through go.py

`./go.py` is the SINGLE entry point for ALL operations. No exceptions.

## Data Flow Architecture

```
User Input Sources:
    Discord ──┐
    Terminal ─┼──→ ./go.py ──→ Service Layer ──→ Claude/Database
    Web ──────┘

Service Layer:
    interactive_service.py - All interactive operations
    discord_service.py - Discord bot management  
    claude_cli_service.py - Claude CLI integration
    database.py - Database operations
```

## How Discord-to-Claude Works

1. **User sends Discord message**
2. **discord_claude_bridge.py receives it** (thin bridge, no logic)
3. **Passes to claude_cli_service.py** (queued processing)
4. **Claude processes naturally** (conversation with context)
5. **Response sent back to Discord**

## Key Modules and Their Purposes

### Entry Point
- **go.py**: The ONLY way to run anything. Manages environment, services, commands.

### Interactive Layer
- **interactive_service.py**: Central hub for ALL interactive features (REPL, chat, queries)
- **claude_chat.py**: Unified chat implementation
- **discord_claude_bridge.py**: Thin Discord-to-Claude bridge

### Data Layer  
- **tournament_models.py**: SQLAlchemy models with 200+ intelligent methods
- **database.py**: Single database connection point
- **polymorphic_queries.py**: Natural language query interface

### Service Layer
- **discord_service.py**: Discord bot service wrapper
- **claude_cli_service.py**: Claude CLI integration (no API keys needed)
- **tournament_operations.py**: Tournament sync and operations

## What Claude Can Do

### In Discord Mode
- Receive messages from users
- Process with conversation context
- Respond naturally about tournaments
- Suggest go.py commands
- Cannot execute code directly

### In Interactive Mode  
- Receive Python objects
- Analyze data structures
- Provide code suggestions
- Full REPL access via chat()

## Available Commands

All through `./go.py`:
- `--discord-bot`: Start Discord bot
- `--ai-chat`: Terminal chat with Claude
- `--interactive`: Python REPL with Claude
- `--sync`: Sync tournaments from start.gg
- `--console`: Display rankings
- `--heatmap`: Generate visualizations
- `--edit-contacts`: Web editor

## Design Principles

1. **Single Entry Point**: Everything through go.py
2. **Thin Bridges**: Service boundaries have zero logic
3. **Intelligent Models**: Objects know their relationships
4. **Natural Language**: Claude handles intent, not syntax
5. **Dynamic Discovery**: Capabilities discovered at runtime

## For Claude: Your Role

You are integrated into this system as the natural language processor. You:
- Receive user messages through various interfaces
- Have knowledge of the tournament tracker system
- Can suggest appropriate go.py commands
- Understand the FGC tournament domain
- Respond conversationally while being helpful

You do NOT:
- Execute database queries directly (you analyze what's given)
- Run Python code in Discord mode (conversation only)
- Access files directly (you work with provided context)

## For Developers: Adding Features

1. ALWAYS add new commands to go.py
2. NEVER create standalone scripts
3. Use interactive_service for interactive features
4. Keep service boundaries thin
5. Document in this file