# Bonjour Integration TODO

## ✅ COMPLETED
- Model Layer (has AnnouncerMixin, announces save/update/delete)
- Database Layer (via bonjour_database.py)
- Query Layer (polymorphic_queries.py)
- Service Layer (Discord, Editor, Claude services)
- Logging Layer (supercharged_logger.py)
- Infrastructure (monitor, discovery, announcer)

## ❌ MISSING BONJOUR - Add These Next:

### 1. Sync/API Layer
- `sync_service.py` - Should announce sync start/complete/errors
- `startgg_sync.py` - Should announce API calls and data fetched

### 2. Calculation Layer  
- `points_system.py` - Should announce point calculations
- `formatters.py` - Should announce formatting operations

### 3. Visualization Layer
- `visualizer.py` - Should announce when generating visualizations
- `tournament_heatmap.py` - Should announce heatmap generation
- `heatmap_advanced.py` - Should announce advanced analytics

### Quick Fix Pattern:
```python
from polymorphic_core import announcer

# At start of operation:
announcer.announce("Service Name", ["Operation starting"])

# At completion:
announcer.announce("Service Name", ["Operation complete", f"Processed {count} items"])
```

## Next Steps:
1. Add announcer imports to missing files
2. Add announce calls at key operations
3. Test with bonjour_monitor.py