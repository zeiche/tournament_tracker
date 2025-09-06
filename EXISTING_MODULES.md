# 📚 EXISTING MODULES AND METHODS - USE THESE, DON'T CREATE NEW ONES!

## ⚠️ CRITICAL: STOP CREATING DUPLICATE MODULES! ⚠️

This document lists ALL existing modules and their methods. **ALWAYS CHECK HERE FIRST** before creating any new functionality.

---

## 🎯 MAIN ENTRY POINT: `go.py`

### Classes and Their Methods:

#### 1. `ProcessManager` - Process/service management
- `find_processes(name)` - Find running processes by name
- `kill_process(pid)` - Kill a specific process
- `kill_all_processes(name, exclude_self=True)` - Kill all matching processes
- `ensure_single_instance(service_name)` - Ensure only one instance runs

#### 2. `ServiceManager` - Systemd service management
- `get_service_status(service_type)` - Get status of a service
- `restart_service(service_type)` - Restart a specific service
- `restart_all_services()` - Restart all services
- `setup_service(service_type, token)` - Setup service with systemd
- `get_discord_service_status()` - Get Discord service status
- `show_all_status()` - Show formatted status of all services

#### 3. `TournamentCommand` - Main tournament operations
- `sync_tournaments(config)` - Sync from start.gg (polymorphic input)
- `generate_console_report(limit)` - Generate console report
- `generate_html_report(output_file, limit)` - Generate HTML report
- `publish_to_shopify(format)` - Publish to Shopify
- `show_shopify_stats()` - Show Shopify statistics
- `generate_heatmaps(input_data)` - Generate visualizations (polymorphic)
- `launch_web_search(port)` - Launch web search interface
- `launch_web_editor(port)` - Launch web editor
- `launch_ai_chat()` - Launch terminal AI chat
- `launch_ai_web(port)` - Launch web AI interface
- `ask_ai(question)` - Ask Claude a single question
- `show_claude_stats()` - Show Claude statistics
- `show_discord_stats()` - Show Discord statistics
- `start_discord_bot(mode)` - Start Discord bot
- `show_statistics()` - Show database statistics
- `identify_organizations()` - Launch org identification
- `launch_interactive_mode()` - Launch interactive mode

#### 4. `CommandLineInterface` - CLI argument parsing
- Handles all command-line arguments and routes to appropriate methods

---

## 📦 CORE MODULES

### `tournament_tracker.py` - Main tracker class
```python
class TournamentTracker:
    - sync_tournaments(page_size, fetch_standings, standings_limit)
    - show_console_report(limit)
    - generate_html_report(limit, output_file)
    - show_statistics()
    - _ensure_db_initialized()
```

### `database_service.py` - Database operations (SINGLE SOURCE)
```python
class DatabaseService:
    - get_organizations_with_stats()
    - get_recent_tournaments(days)
    - get_player_rankings(limit)
    - get_tournament_by_id(tournament_id)
    - search_tournaments(query)
    - search_players(query)
```

### `log_manager.py` - Centralized logging
```python
class LogManager:
    - get_logger(name)
    - context(context_name)
    - log_exception(exception, context)
```

---

## 🎨 VISUALIZATION MODULES

### `visualizer.py` - Unified visualization (POLYMORPHIC)
```python
# Main functions (accept ANY input):
- visualize(data, output_file) - Smart visualization based on data type
- heatmap(data, output_file, **options) - Generate heatmaps
- chart(data, output_file, **options) - Generate charts
- table(data, output_file, **options) - Generate tables

class UnifiedVisualizer:
    - render_html(data, template)
    - render_table(data)
    - render_heatmap(data)
    - save_page(content, filename)
```

---

## 🛍️ SHOPIFY MODULES

### `publish_operation.py` - Main publishing orchestrator
```python
class PublishOperation:
    - execute() - Main publish method
    - _gather_tournament_data()
    - _generate_outputs(data)
    - _publish_to_shopify(outputs) - Updates /pages/attendance ONLY!

# Convenience functions:
- publish_to_shopify(**kwargs)
- generate_rankings_html()
```

### `tournament_report.py` - Theme template updater
```python
- find_store_and_theme() - Get Shopify configuration
- update_template(store_url, theme_id, token, html, ...) - Update page.attendance.json
- format_html_table(attendance_tracker, org_names) - Format HTML
```

### ⚠️ DEPRECATED: `shopify_separated_publisher.py`
**DO NOT USE** - Creates new pages which violates our rules!

---

## 🤖 AI/CLAUDE MODULES

### `claude_service.py` - Claude AI service (SINGLE SOURCE)
```python
class ClaudeService:
    - is_enabled() - Check if service is enabled
    - ask_question(question, context) - Ask a question
    - start_terminal_chat() - Start terminal chat
    - start_web_chat(port) - Start web chat
    - get_statistics() - Get usage statistics
```

### `claude_cli_service.py` - CLI integration
```python
class ClaudeCLIService:
    - process_message(message) - Process via Claude CLI
    - start_interactive() - Start interactive mode
```

---

## 💬 DISCORD MODULES

### `discord_service.py` - Discord service (SINGLE SOURCE)
```python
# Main functions:
- start_discord_bot(mode) - Start the bot
- is_discord_enabled() - Check if enabled
- get_statistics() - Get bot statistics

class DiscordService:
    - handle_message(message) - Process Discord messages
    - send_response(channel, response) - Send responses
```

### `discord_bridge.py` - Thin message forwarder
```python
# Simple 100-line bridge that forwards to Claude
- on_message(message) - Forward to Claude
- on_ready() - Bot ready handler
```

### `polymorphic_queries.py` - Natural language queries
```python
- query(text) - Process any natural language query
- show_player(name) - Show player stats
- show_organization(name) - Show org stats
- show_recent_tournaments() - Show recent events
```

---

## 🗄️ DATABASE MODELS

### `tournament_models.py` - Enhanced ORM models (200+ methods!)
```python
class Tournament(Base, LocationMixin, TimestampMixin):
    # Properties:
    - has_location, coordinates, days_ago, is_recent, is_major
    # Methods:
    - distance_to(lat, lng)
    - get_heatmap_weight()
    - calculate_growth(other)
    # Class methods:
    - get_major_tournaments(session)
    - get_recent(session, days)

class Player(Base):
    # Properties:
    - win_rate, podium_rate, points_per_event, consistency_score
    # Methods:
    - get_tournaments(session)
    - get_placements(session)
    - calculate_trajectory()

class Organization(Base):
    # Methods:
    - get_tournaments(session)
    - get_contacts()
    - add_contact(type, value)
    - merge_into(target_org)
```

---

## 🔧 UTILITY MODULES

### `polymorphic_inputs.py` - Input handling
```python
class InputHandler:
    - parse(input_data, expected_type) - Parse any input
    
# Decorators:
@accepts_anything(param_name) - Accept any input type
@to_list(input_data) - Convert to list
@to_dict(input_data) - Convert to dict
@to_ids(input_data) - Extract IDs
```

### `editor_service.py` - Web editor service
```python
class EditorService:
    - run_blocking() - Start web editor
    - handle_request(request) - Process web requests
    - update_organization(org_id, data)
    - merge_organizations(source_id, target_id)
```

---

## 🚫 COMMON DUPLICATE PATTERNS TO AVOID

### ❌ DON'T CREATE these (they already exist):

1. **Database connection handlers** - Use `DatabaseService`
2. **Logging utilities** - Use `LogManager`
3. **Shopify publishers** - Use `publish_operation.py`
4. **Discord bots** - Use `discord_service.py`
5. **Claude/AI interfaces** - Use `claude_service.py`
6. **Visualization generators** - Use `visualizer.py`
7. **HTML generators** - Use `UnifiedVisualizer`
8. **Process managers** - Use `ProcessManager` from go.py
9. **Service managers** - Use `ServiceManager` from go.py
10. **Query handlers** - Use `polymorphic_queries.py`

### ✅ DO THIS INSTEAD:

```python
# WRONG - Creating new database handler
class MyDatabaseHandler:
    def get_tournaments():
        # Duplicate code!

# RIGHT - Use existing
from database_service import DatabaseService
db = DatabaseService()
tournaments = db.get_recent_tournaments(days=30)
```

```python
# WRONG - Creating new visualizer
def create_heatmap(data):
    # Duplicate code!

# RIGHT - Use existing
from visualizer import heatmap
result = heatmap(data, "output.html")
```

```python
# WRONG - Creating new Discord bot
class MyDiscordBot:
    # Duplicate code!

# RIGHT - Use existing
from discord_service import start_discord_bot
start_discord_bot()
```

---

## 📋 CHECKLIST BEFORE CREATING NEW CODE

1. ✓ Check `EXISTING_MODULES.md` (this file)
2. ✓ Check if `go.py` already has a command for it
3. ✓ Check if `database_service.py` has the query
4. ✓ Check if `visualizer.py` can handle the visualization
5. ✓ Check if `tournament_models.py` has the method
6. ✓ Check if `polymorphic_queries.py` can answer it

**If any of these have what you need, USE IT!**

---

Last Updated: 2025-09-06
This file exists because we keep creating duplicate modules instead of using existing ones.