# 📖 Module Usage Quick Reference Guide

## For Every Common Task, Use These Modules:

### 🗄️ Database Operations
**Module**: `database_service.py` or `database.py`
```python
from database_service import DatabaseService
db = DatabaseService()
# OR
from database import session_scope
with session_scope() as session:
    # queries
```

### 🎨 HTML/Visualization Generation
**Module**: `visualizer.py`
```python
from visualizer import UnifiedVisualizer, visualize, heatmap
viz = UnifiedVisualizer()
result = viz.render(data)
# OR
result = visualize(data, "output.html")
```

### 🛍️ Shopify Publishing
**Module**: `publish_operation.py` → `tournament_report.py`
```python
from publish_operation import PublishOperation
op = PublishOperation()
result = op.execute()  # This updates /pages/attendance ONLY
```

### 💬 Discord Bot
**Module**: `discord_service.py`
```python
from discord_service import start_discord_bot
start_discord_bot()
```

### 🤖 AI/Claude Integration
**Module**: `claude_service.py`
```python
from claude_service import claude_service
result = claude_service.ask_question("question")
```

### 📝 Logging
**Module**: `log_manager.py`
```python
from log_manager import LogManager
logger = LogManager().get_logger('module_name')
logger.info("message")
```

### 🔧 Process Management
**Module**: `go.py` classes
```python
from go import ProcessManager, ServiceManager
ProcessManager.ensure_single_instance('service')
ServiceManager.restart_service(ServiceType.WEB)
```

### 🎯 Main Entry Point
**Module**: `go.py`
```bash
./go.py --sync           # Sync tournaments
./go.py --publish         # Publish to Shopify
./go.py --heatmap         # Generate visualizations
./go.py --edit-contacts   # Launch web editor
```

## ❌ NEVER Create New Modules For:

1. **Database connections** - Use `DatabaseService` or `database.py`
2. **HTML generation** - Use `visualizer.py`
3. **Shopify API calls** - Use `publish_operation.py`
4. **Discord bots** - Use `discord_service.py`
5. **Logging utilities** - Use `log_manager.py`
6. **Process management** - Use `go.py` classes
7. **Query handlers** - Use `polymorphic_queries.py`
8. **Tournament operations** - Use `tournament_tracker.py`

## 📁 Deprecated Modules (DO NOT USE):

These have been renamed to `.bak` to prevent usage:
- ❌ `database_utils.py` → Use `database_service.py`
- ❌ `session_utils.py` → Use `database.py`
- ❌ `shopify_separated_publisher.py` → Use `publish_operation.py`
- ❌ `log_utils.py` → Use `log_manager.py`

## 🔍 Before Creating ANY New Code:

1. Check `EXISTING_MODULES.md` for complete module list
2. Check `MODULE_USAGE_GUIDE.md` (this file) for which module to use
3. Check if `go.py` already has a command for it
4. Search existing modules for similar functionality

## 📋 Common Patterns:

### Pattern 1: Database Query
```python
# WRONG - Creating new database handler
def get_my_data():
    session = create_session()  # NO!
    
# RIGHT - Use existing service
from database_service import DatabaseService
db = DatabaseService()
data = db.get_recent_tournaments(30)
```

### Pattern 2: HTML Generation
```python
# WRONG - Creating new HTML generator
def make_html(data):
    html = "<html>..."  # NO!
    
# RIGHT - Use visualizer
from visualizer import UnifiedVisualizer
viz = UnifiedVisualizer()
html = viz.render(data)
```

### Pattern 3: Shopify Update
```python
# WRONG - Direct Shopify API call
requests.post(shopify_url, ...)  # NO!

# RIGHT - Use publish operation
from publish_operation import PublishOperation
op = PublishOperation()
op.execute()
```

---

## Summary: ONE MODULE PER DOMAIN

- **Database**: `database_service.py`
- **Visualization**: `visualizer.py`
- **Shopify**: `publish_operation.py`
- **Discord**: `discord_service.py`
- **Claude AI**: `claude_service.py`
- **Logging**: `log_manager.py`
- **Entry Point**: `go.py`

**USE THESE. DON'T CREATE NEW ONES.**

---
Last Updated: 2025-09-06