# Pythonic Refactoring Priority List

## 🎯 Refactoring Status
- ✅ **DONE**: Already refactored to be Pythonic
- 🔧 **NEEDS WORK**: Requires Pythonic refactoring
- ⚠️ **LEGACY**: Old code that should be replaced/removed

---

## ✅ Already Pythonic (Completed)

### Single Source of Truth Services (SSOT)
1. ✅ `database.py` - SSOT for database connections
2. ✅ `claude_service.py` - SSOT for Claude/AI operations  
3. ✅ `discord_service.py` - SSOT for Discord bot
4. ✅ `shopify_service.py` - SSOT for Shopify publishing
5. ✅ `tournament_models.py` - Enhanced with magic methods, cached_property, proper exceptions

### OOP Refactored
6. ✅ `html_renderer.py` - OOP HTML generation
7. ✅ `log_manager.py` - OOP logging with singleton

---

## 🔴 HIGH PRIORITY - Core Utilities (Week 1)

These are used everywhere and need immediate attention:

### 1. 🔧 `database_utils.py` (28 functions)
**Issues**: Procedural functions, no classes, repeated code
**Fix**: Convert to DatabaseService class with methods
**Impact**: HIGH - Used by all models

### 2. 🔧 `log_utils.py` (12 functions)  
**Issues**: Global state, procedural logging
**Fix**: Should use log_manager.py instead
**Impact**: HIGH - Used everywhere

### 3. 🔧 `session_utils.py` (14 functions)
**Issues**: Procedural session management
**Fix**: Merge into database.py SSOT
**Impact**: HIGH - Database session handling

### 4. 🔧 `startgg_client.py`
**Issues**: Not using proper class structure, error handling
**Fix**: Create StartGGService class with retry logic, caching
**Impact**: HIGH - API client for all tournament data

### 5. 🔧 `startgg_query.py` 
**Issues**: Procedural GraphQL queries
**Fix**: QueryBuilder class with fluent interface
**Impact**: HIGH - Core data fetching

---

## 🟡 MEDIUM PRIORITY - Business Logic (Week 2)

### 6. 🔧 `tournament_tracker.py`
**Issues**: Mixed responsibilities, could use better patterns
**Fix**: Separate into TournamentService, SyncService, ReportService
**Impact**: MEDIUM - Main business logic

### 7. 🔧 `sync_operation.py` / `sync_operation_v2.py`
**Issues**: Duplicate files, procedural
**Fix**: Consolidate into single SyncService class
**Impact**: MEDIUM - Tournament synchronization

### 8. 🔧 `discord_conversational.py`
**Issues**: Giant if-elif chains for commands
**Fix**: Command pattern with registry
**Impact**: MEDIUM - Discord bot logic

### 9. 🔧 `tournament_operations.py`
**Issues**: Procedural operations
**Fix**: OperationsManager class with strategy pattern
**Impact**: MEDIUM - Tournament operations

### 10. 🔧 `web_editor.py` / `editor.py` / `editor_core.py`
**Issues**: Three files for same functionality
**Fix**: Consolidate into single EditorService
**Impact**: MEDIUM - Web interface

---

## 🟢 LOW PRIORITY - Utilities & Scripts (Week 3)

### 11. 🔧 `html_utils.py` (9 functions)
**Issues**: Procedural HTML generation
**Fix**: Should use html_renderer.py instead
**Impact**: LOW - Being replaced

### 12. 🔧 `operation_utils.py`
**Issues**: Procedural utility functions
**Fix**: OperationHelper class or merge into services
**Impact**: LOW - Helper utilities

### 13. 🔧 `database_queue.py`
**Issues**: Not following queue patterns
**Fix**: Proper Queue class with context manager
**Impact**: LOW - Queue management

### 14. 🔧 `publish_operation.py`
**Issues**: Should use shopify_service.py
**Fix**: Remove and use SSOT service
**Impact**: LOW - Being replaced

### 15. 🔧 `ai_service.py` / `ai_web_chat.py`
**Issues**: Should use claude_service.py
**Fix**: Remove and use SSOT service
**Impact**: LOW - Being replaced

---

## 🗑️ CLEANUP - Remove/Consolidate (Week 4)

### Files to Remove (duplicates/legacy):
- ⚠️ `tournament_models_enhanced.py` - Duplicate of tournament_models.py
- ⚠️ `tournament_models_complete.py` - Another duplicate
- ⚠️ `shopify_query.py` - Use shopify_service.py
- ⚠️ `shopify_publish.py` - Use shopify_service.py
- ⚠️ `sync_operation_v2.py` - Merge with sync_operation.py
- ⚠️ `demo_repl.py` - Test file
- ⚠️ `test_*.py` files - Move to tests/ directory

### Files to Consolidate:
- `editor.py` + `editor_core.py` + `web_editor.py` → `editor_service.py`
- `html_utils.py` → Use `html_renderer.py`
- `log_utils.py` → Use `log_manager.py`
- `session_utils.py` → Use `database.py`

---

## 📋 Pythonic Patterns to Apply

### 1. **Replace Procedural with OOP**
```python
# Bad (current)
def get_tournament(id):
    session = get_session()
    return session.query(Tournament).get(id)

# Good (Pythonic)
class TournamentService:
    def get(self, id: str) -> Optional[Tournament]:
        with self.session_scope() as session:
            return session.query(Tournament).get(id)
```

### 2. **Use Context Managers**
```python
# Bad
session = get_session()
try:
    # do stuff
finally:
    session.close()

# Good
with session_scope() as session:
    # do stuff
```

### 3. **Replace if-elif with Registry/Strategy**
```python
# Bad
if command == "help":
    return help()
elif command == "status":
    return status()

# Good
@command_registry.register("help")
def help_command():
    return "Help text"
```

### 4. **Use Type Hints & Dataclasses**
```python
# Good
@dataclass
class SyncResult:
    success: bool
    tournaments_synced: int
    errors: List[str]
    duration: timedelta
```

### 5. **Single Source of Truth Pattern**
```python
# Every service should be a singleton
class ServiceName:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

---

## 🚀 Refactoring Order

### Week 1: Core Infrastructure
1. Fix database_utils.py → DatabaseService
2. Fix log_utils.py → Use log_manager.py  
3. Fix session_utils.py → Merge into database.py
4. Fix startgg_client.py → StartGGService
5. Fix startgg_query.py → QueryBuilder

### Week 2: Business Logic  
6. Refactor tournament_tracker.py
7. Consolidate sync operations
8. Fix discord_conversational.py
9. Clean up tournament_operations.py
10. Consolidate editor files

### Week 3: Utilities
11. Remove html_utils.py
12. Fix operation_utils.py
13. Fix database_queue.py
14. Remove duplicate publish files
15. Remove duplicate AI files

### Week 4: Cleanup
- Remove all duplicate model files
- Move tests to tests/ directory
- Remove legacy code
- Update imports everywhere

---

## 📊 Metrics

- **Total Python files**: 75
- **Already Pythonic**: 7 files (9%)
- **Need refactoring**: 35 files (47%)
- **To remove/consolidate**: 33 files (44%)

## 🎯 Goal

Transform the codebase from ~50% procedural C-style code to 100% Pythonic OOP code with:
- Single Source of Truth for all services
- Proper OOP patterns throughout
- Type hints on all functions
- Context managers for resources
- No global state
- Clean separation of concerns