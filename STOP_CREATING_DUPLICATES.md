# 🛑 STOP! DON'T CREATE NEW MODULES!

## We Have a SERIOUS Problem

We keep creating duplicate modules that do the same thing. This MUST STOP.

## Before You Write ANY New Code:

### 1️⃣ Check These Documents (IN THIS ORDER):
1. **`EXISTING_MODULES.md`** - Complete list of all modules and their methods
2. **`MODULE_USAGE_GUIDE.md`** - Quick reference for which module to use
3. **`MIGRATION_FROM_DEPRECATED.md`** - How to migrate from old modules

### 2️⃣ For Common Tasks, Use These:

| Task | Use This Module | NOT These |
|------|----------------|-----------|
| Database queries | `database_service.py` | ❌ database_utils, session_utils |
| HTML generation | `visualizer.py` | ❌ html_renderer, html_utils |
| Shopify publishing | `publish_operation.py` | ❌ shopify_separated_publisher |
| Discord bot | `discord_service.py` | ❌ Multiple Discord implementations |
| Logging | `log_manager.py` | ❌ log_utils, raw logging |
| Process management | `go.py` classes | ❌ Custom process handlers |

### 3️⃣ The Module Exists - Find It!

**99% of the time, the functionality you need ALREADY EXISTS.**

Examples of things that ALREADY EXIST:
- Database connection management
- Session handling
- HTML table generation
- Heatmap creation
- Shopify page updates
- Discord message handling
- Tournament syncing
- Player rankings
- Organization management
- Web editors
- AI chat interfaces

### 4️⃣ How to Find Existing Functionality:

```bash
# Search for a method
grep -r "method_name" /home/ubuntu/claude/tournament_tracker/

# Look at main entry point
less /home/ubuntu/claude/tournament_tracker/go.py

# Check the database service
less /home/ubuntu/claude/tournament_tracker/database_service.py

# Check the visualizer
less /home/ubuntu/claude/tournament_tracker/visualizer.py
```

## 🚨 RED FLAGS - If You're Doing These, STOP:

1. **Creating a new file ending in `_utils.py`** - The utils probably exist
2. **Writing HTML generation code** - Use `UnifiedVisualizer`
3. **Opening a database session** - Use `DatabaseService`
4. **Making Shopify API calls** - Use `PublishOperation`
5. **Setting up logging** - Use `LogManager`
6. **Creating a Discord bot class** - Use `discord_service`

## ✅ The Right Way:

```python
# Step 1: Check if it exists
# Look in EXISTING_MODULES.md

# Step 2: Import the existing module
from database_service import DatabaseService
from visualizer import UnifiedVisualizer
from publish_operation import PublishOperation

# Step 3: Use it
db = DatabaseService()
viz = UnifiedVisualizer()
pub = PublishOperation()

# Step 4: If it truly doesn't exist (rare!), extend the existing module
# Don't create a new one!
```

## 📊 Current Status:

- **Deprecated modules removed**: 3
- **Duplicate patterns identified**: 5+
- **Modules that do the same thing**: Too many!

## 🎯 Goal:

**ONE module per domain. NO duplicates. NO exceptions.**

---

## Remember:

> "Every time you create a duplicate module, you make the codebase harder to maintain, harder to debug, and harder to understand. CHECK FIRST. CREATE NEVER."

---

Last Updated: 2025-09-06
This is the FOURTH document created to stop duplicate modules. Please let it be the last.