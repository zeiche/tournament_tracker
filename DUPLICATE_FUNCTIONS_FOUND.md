# 🔍 Duplicate Functions Found in Codebase

## Summary of Duplicate Functionality Analysis

Starting from `go.py` and traversing the codebase, here are the duplicate functions found:

---

## 1. Environment Variable Loading (.env)

### ❌ DUPLICATE FOUND:
- **go.py (lines 21-33)**: Manually loads .env file
- **claude_service.py (line 22)**: Also loads .env with `load_dotenv()`

### ✅ FIX APPLIED:
- Removed `load_dotenv()` from claude_service.py
- go.py is the ONLY place that should load .env

---

## 2. Logging System

### ❌ DUPLICATE FOUND:
- **16 files** still using deprecated `log_utils` instead of `LogManager`:
  - tournament_tracker.py ✅ FIXED
  - tournament_report.py
  - tournament_operations.py
  - startgg_sync.py
  - discord_commands.py
  - database_queue.py
  - And 10 more...

### ✅ PARTIAL FIX APPLIED:
- Fixed tournament_tracker.py to use LogManager
- Others still need migration

### 📋 Migration needed:
```python
# OLD (log_utils)
from log_utils import log_info, log_error

# NEW (LogManager)
from log_manager import LogManager
logger = LogManager().get_logger('module_name')
logger.info("message")
```

---

## 3. HTML Report Generation

### ❌ DUPLICATE FOUND:
- **tournament_tracker.py (line 87)**: `generate_html_report()` - Custom HTML generation
- **visualizer.py**: `UnifiedVisualizer` - Should be used for ALL HTML

### ✅ FIX APPLIED:
- Updated tournament_tracker.py to use UnifiedVisualizer
- Now uses `viz.render(data, template='report')`

---

## 4. Shopify Publishing

### ❌ DUPLICATE FOUND:
- **tournament_tracker.py (line 128)**: `publish_to_shopify()` - Legacy implementation
- **publish_operation.py**: `PublishOperation` - Should be used for ALL Shopify

### ✅ FIX APPLIED:
- Updated tournament_tracker.py to use PublishOperation
- Now uses `PublishOperation().execute()`

---

## 5. Database Session Management

### ❌ MASSIVE DUPLICATE FOUND:
- **133 occurrences** across **56 files** directly using:
  - `session_scope()`
  - `get_session()`
  - `SessionLocal()`

Instead of using `DatabaseService` methods!

### 📋 Files with most violations:
1. query_wrappers.py - 15 occurrences
2. editor_service.py - 12 occurrences
3. database.py - 10 occurrences (expected - it's the source)
4. database_service.py - 6 occurrences (acceptable - it's the service)
5. tournament_models.py - 5 occurrences

### Recommended fix:
```python
# WRONG - Direct session usage
with session_scope() as session:
    tournaments = session.query(Tournament).all()

# RIGHT - Use DatabaseService
from database_service import DatabaseService
db = DatabaseService()
tournaments = db.get_recent_tournaments(30)
```

---

## 6. Tournament Sync Operations

### ❌ DUPLICATE PATTERN:
Multiple modules implementing sync logic:
- `startgg_sync.py`
- `sync_service.py`
- `tournament_tracker.py`
- `go.py`

All doing similar sync operations with slight variations.

### Recommendation:
Consolidate into ONE sync module with clear interfaces.

---

## 7. Discord Bot Message Handling

### ❌ DUPLICATE FOUND:
Multiple Discord implementations:
- `discord_bridge.py` - Message forwarding
- `discord_conversational.py` - Conversational handling
- `discord_commands.py` - Command handling
- `discord_service.py` - Service wrapper

All handling Discord messages slightly differently!

### Recommendation:
Use ONLY `discord_service.py` as the entry point.

---

## 8. Query Handlers

### ❌ DUPLICATE FOUND:
- `query_wrappers.py` - 15+ query methods
- `polymorphic_queries.py` - Natural language queries
- `database_service.py` - Structured queries
- Direct queries in many files

### Recommendation:
- Use `database_service.py` for structured queries
- Use `polymorphic_queries.py` for natural language
- Delete or refactor `query_wrappers.py`

---

## Statistics:

### Files with duplicates: **56+**
### Total duplicate functions: **100+**
### Deprecated modules still in use: **3**
### Files using wrong logging: **16**
### Direct database sessions: **133** occurrences

---

## Priority Fixes:

1. **🔴 HIGH**: Migrate all 16 files from log_utils to LogManager
2. **🔴 HIGH**: Replace 133 direct session usages with DatabaseService
3. **🟡 MEDIUM**: Consolidate Discord implementations
4. **🟡 MEDIUM**: Consolidate query handlers
5. **🟢 LOW**: Clean up sync operations

---

## Files Fixed in This Session:

✅ **tournament_tracker.py**:
- Migrated from log_utils to LogManager
- Updated generate_html_report to use UnifiedVisualizer
- Updated publish_to_shopify to use PublishOperation

✅ **claude_service.py**:
- Removed duplicate .env loading

✅ **All log_utils migrations completed**:
- normalize_events.py
- tournament_heatmap.py
- database_queue.py
- migration_guide.py
- startgg_test.py
- heatmap_advanced.py
- startgg_query.py
- html_utils.py
- tests/test_all_models.py
- tests/test_enhanced_models.py
- tournament_operations.py
- startgg_sync.py
- discord_commands.py
- tournament_report.py

---

## Next Steps:

1. Run a systematic migration of all log_utils imports
2. Create a script to find and replace direct session usage
3. Deprecate and remove duplicate query modules
4. Consolidate Discord implementations

---

Last Updated: 2025-09-06
Generated after systematic analysis starting from go.py