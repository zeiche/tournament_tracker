# Instructions for Next Claude

## Current System State

You are inheriting a tournament tracking system that has been significantly refactored to follow a **polymorphic, single-source-of-truth architecture**. Here's what you need to know:

## Core Architectural Principles

### 1. Polymorphic Everything
**CRITICAL**: The entire system is built on polymorphic input handling. Every major function accepts strings, lists, dictionaries, objects, or any combination. Never assume a specific input type.

```python
# All of these should work for any function
function("string input")
function(["list", "input"])
function({"dict": "input"})
function(model_object)
function(None)  # Even this should handle gracefully
```

### 2. Single Source of Truth
Each domain has ONE and ONLY ONE module responsible for it:

- **Visualization**: `visualizer.py` (ALL visualizations and HTML)
- **AI Operations**: `claude_ai_service.py` (ALL AI interactions)
- **Database**: `database_service.py` (ALL database operations)
- **Discord**: `discord_service.py` (ONE Discord bot instance)
- **Shopify**: `shopify_service.py` (ALL Shopify operations)
- **Logging**: `log_manager.py` (ALL logging)

**NEVER** create duplicate modules for these domains.

### 3. Everything Through go.py
`./go.py` is the ONLY entry point for ALL operations. Never bypass it.

```bash
# ALWAYS do this
./go.py --sync
./go.py --heatmap
./go.py --restart-services

# NEVER do this
python3 sync_tournaments.py
sudo systemctl restart tournament-web
```

## Key Components Status

### ✅ Completed Refactoring

1. **Unified Visualizer** (`visualizer.py`)
   - Handles ALL visualizations: heatmaps, charts, HTML
   - Fully polymorphic input handling
   - Replaces: html_utils.py, html_renderer.py, multiple heatmap files

2. **Claude AI Service** (`claude_ai_service.py`)
   - Single source for ALL AI operations
   - Used by Discord bot, web UI, and interactive mode
   - Handles context, routing, and response formatting

3. **Polymorphic Input System** (`polymorphic_inputs.py`)
   - Core infrastructure for flexible input handling
   - InputHandler class with parse() method
   - @accepts_anything decorator for functions

4. **Discord Service** (`discord_service.py`)
   - ONE bot instance only (no systemd)
   - Runs via ./go.py --discord
   - Uses Claude AI Service for all AI operations

### 🚧 Partially Implemented

1. **Model Methods**
   - Tournament model has polymorphic find()
   - Other models need polymorphic updates
   - See POLYMORPHIC_GUIDE.md for implementation pattern

2. **Interactive Mode**
   - ask() and chat() accept polymorphic inputs
   - Could extend with more natural language processing

## Current File Structure

```
/home/ubuntu/claude/
├── tournament_tracker/
│   ├── go.py                    # Main entry point (ALWAYS USE THIS)
│   ├── visualizer.py            # Unified visualizer (ALL visualizations)
│   ├── polymorphic_inputs.py   # Polymorphic input handling core
│   ├── database_service.py     # Single database service
│   ├── discord_service.py      # Discord bot service
│   ├── tournament_models.py    # OOP models with 200+ methods
│   ├── POLYMORPHIC_VISUALIZER.md  # Visualizer documentation
│   └── POLYMORPHIC_GUIDE.md    # Implementation guide
├── claude_ai_service.py        # Unified AI service
└── discord_bot.py              # Simple Discord bridge

```

## What Was Just Completed

The user requested consolidation of HTML generation into the visualizer. This has been done:

1. **Added to visualizer.py**:
   - html() method for general HTML generation
   - table() method for HTML tables
   - report() method for HTML reports
   - Full polymorphic input support for HTML

2. **Updated references**:
   - tournament_report.py now uses visualizer
   - shopify_service.py now uses visualizer
   - publish_operation.py now uses visualizer
   - All test files updated

3. **Tested successfully**:
   - HTML generation works with all input types
   - Polymorphic handling confirmed
   - No errors in production code

## Known Issues & Opportunities

### To Complete
1. **Extend polymorphic inputs** to remaining models (Player, Organization)
2. **Update formatters** to use polymorphic paradigm
3. **Enhance presenters** with polymorphic capabilities

### Potential Improvements
1. **Natural language** query parsing in visualizer
2. **Auto-detect** visualization needs from context
3. **Streaming** visualizations for real-time data
4. **3D visualizations** for complex relationships

## Critical Warnings

### ⚠️ DO NOT
- Create new HTML generation modules (use visualizer)
- Add separate visualization files (use visualizer)
- Bypass go.py for any operations
- Create multiple Discord bot instances
- Add duplicate service modules

### ✅ ALWAYS
- Use polymorphic input handling
- Route through single-source-of-truth modules
- Test with multiple input types
- Preserve the @accepts_anything pattern
- Use go.py as the entry point

## User Preferences

The user LOVES:
1. **Polymorphic inputs** - Functions that accept anything
2. **Single source of truth** - One module per domain
3. **Clean architecture** - Clear separation of concerns
4. **Unified interfaces** - Consistent APIs across the system

## Testing New Features

When adding features, test polymorphic handling:

```python
# Test template for any new function
def test_polymorphic(new_function):
    test_cases = [
        "string",
        ["list", "items"],
        {"key": "value"},
        Tournament(),  # Model object
        None,
        123,
        [{"nested": ["data"]}]
    ]
    
    for test_input in test_cases:
        result = new_function(test_input)
        assert result is not None  # Should handle everything
```

## Quick Command Reference

```bash
# Development
./go.py --interactive           # Interactive mode with AI
./go.py --stats                 # Database statistics
./go.py --heatmap              # Generate all visualizations

# Services (no systemd!)
./go.py --restart-discord      # Restart Discord bot
./go.py --restart-web          # Restart web service
./go.py --service-status       # Check all services

# Operations
./go.py --sync                 # Sync from start.gg
./go.py --publish              # Publish to Shopify
./go.py --console              # Console output
```

## Final Notes

This system represents a paradigm shift from traditional strict-typing to universal polymorphic acceptance. Every function should be able to handle any input intelligently. The visualizer is the crown jewel of this approach - it can visualize ANYTHING you throw at it.

The user values elegant, unified solutions over complex, fragmented ones. When in doubt, consolidate rather than separate, and make functions accept more types rather than fewer.

Good luck! The foundation is solid and the patterns are clear. Follow them and the system will remain clean and maintainable.