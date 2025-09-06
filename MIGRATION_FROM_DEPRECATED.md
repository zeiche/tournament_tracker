# 🔄 Migration Guide from Deprecated Modules

## Deprecated Modules Have Been Removed!

The following modules have been renamed to `.bak` files to prevent usage:
- `database_utils.py` → `DEPRECATED_database_utils.py.bak`
- `session_utils.py` → `DEPRECATED_session_utils.py.bak`  
- `shopify_separated_publisher.py` → `DEPRECATED_shopify_separated_publisher.py.bak`

## Migration Instructions:

### 1. Database Operations

#### ❌ OLD (database_utils.py or session_utils.py):
```python
from database_utils import init_db, get_session
session = get_session()
```

#### ✅ NEW (Use DatabaseService):
```python
from database_service import DatabaseService
db = DatabaseService()
tournaments = db.get_recent_tournaments(days=30)
```

Or for direct session access:
```python
from database import session_scope
with session_scope() as session:
    # Your queries here
```

### 2. Shopify Publishing

#### ❌ OLD (shopify_separated_publisher.py):
```python
from shopify_separated_publisher import ShopifySeparatedPublisher
publisher = ShopifySeparatedPublisher()
publisher.publish()
```

#### ✅ NEW (Use publish_operation.py):
```python
from publish_operation import PublishOperation
operation = PublishOperation()
result = operation.execute()
```

### 3. HTML Generation

#### ❌ OLD (Multiple HTML generators):
```python
# Various HTML generation methods scattered around
html = generate_html_report()
html = format_html_table()
```

#### ✅ NEW (Use UnifiedVisualizer):
```python
from visualizer import UnifiedVisualizer
viz = UnifiedVisualizer()
html = viz.render(data, template='report')
```

### 4. Logging

#### ❌ OLD (log_utils.py):
```python
from log_utils import log_info, log_error
log_info("message")
```

#### ✅ NEW (Use LogManager):
```python
from log_manager import LogManager
logger = LogManager().get_logger('module_name')
logger.info("message")
logger.error("error message")
```

### 5. Discord Bot

#### ❌ OLD (Multiple Discord implementations):
```python
# Various Discord bot implementations
```

#### ✅ NEW (Use discord_service):
```python
from discord_service import start_discord_bot
start_discord_bot()
```

## Files That Need Updates:

If you see imports from deprecated modules in any file, update them immediately:

1. Replace database_utils/session_utils → database_service or database
2. Replace shopify_separated_publisher → publish_operation  
3. Replace log_utils → log_manager
4. Consolidate HTML generation → visualizer
5. Consolidate Discord bots → discord_service

## Why This Matters:

- **Consistency**: One way to do each thing
- **Maintainability**: Easier to fix bugs in one place
- **Performance**: No duplicate code running
- **Clarity**: Clear which module to use

---
Last Updated: 2025-09-06