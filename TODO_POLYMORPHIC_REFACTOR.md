# TODO: The Great Polymorphic Refactor - ask/tell/do Everything! 🎯

## Mission: Convert ALL Modules from 200+ Methods to Just 3

We're on a quest to transform the entire codebase from traditional OOP (with hundreds of specific methods) to a polymorphic pattern where EVERYTHING uses just **ask()**, **tell()**, and **do()**.

## 🏆 The Goal

**BEFORE**: 237+ different method names to remember
```python
tournament.get_winner()
tournament.get_top_8_placements() 
discord.connect()
mixer.start_continuous_music()
database.get_player_by_id()
sync.fetch_recent_tournaments()
# ... 200+ more methods to memorize
```

**AFTER**: Just 3 universal methods that understand intent
```python
tournament.ask("winner")
tournament.ask("top 8")
discord.do("connect")
mixer.do("start music")
database.ask("player 123")
sync.do("fetch recent")
# Everything uses ask/tell/do!
```

## ✅ Completed Conversions

### Models (Broken up from 2736-line monster file!)
- [x] **tournament_models.py** → Split into:
  - `models/tournament_model.py` (250 lines)
  - `models/player_model.py` (280 lines)
  - `models/organization_model.py` (290 lines)
  - `models/mixins.py` (60 lines)
  - **Reduction**: 66% fewer lines, 99% fewer methods!

### Core Infrastructure
- [x] **universal_polymorphic.py** - Base class for everything
- [x] **go_polymorphic.py** - Entry point using ask/tell/do
- [x] **demo_polymorphic.py** - Demonstration of the pattern

### Services
- [x] **database_service.py** - Already had ask/tell/do!
- [x] **sync_service.py** → `sync_service_polymorphic.py`
- [x] **bonjour_discord.py** → `bonjour_discord_polymorphic.py`
- [x] **bonjour_audio_mixer.py** → `bonjour_audio_mixer_polymorphic.py`

### Bridge Services
- [x] **discord_polymorphic.py** - Discord bridge with ask/tell/do
- [x] **twilio_polymorphic.py** - Twilio bridge with ask/tell/do

## 🔴 Still Need Conversion (40+ modules!)

### High Priority Services
- [ ] **startgg_service.py** - API integration
- [ ] **editor_service.py** - Web editor
- [ ] **claude_chat.py** - Claude AI interface
- [ ] **heatmap_advanced.py** - Visualization

### Bonjour Services
- [ ] **bonjour_twilio.py** - Telephony
- [ ] **bonjour_monitor.py** - System monitor
- [ ] **dynamic_command_discovery.py** - Command routing
- [ ] **bonjour_database.py** - Database wrapper
- [ ] **bonjour_audio_detector.py** - Audio detection

### Utility Modules
- [ ] **fuzzy_search.py** - Search functionality
- [ ] **conversational_search.py** - Natural language search
- [ ] **identify_organizations.py** - Org identification
- [ ] **log_manager.py** - Logging
- [ ] **shutdown_coordinator.py** - Shutdown management

### Original Files to Replace
- [ ] **go.py** - Still using old pattern (replace with go_polymorphic.py)
- [ ] **bonjour_discord.py** - Replace with polymorphic version
- [ ] **tournament_tracker.py** - Main tracker logic

## 📊 Progress Tracking

**Total Modules**: ~50
**Converted**: 12 (24%)
**Remaining**: 38 (76%)

## 🛑 Critical Rules During Refactor

1. **PRESERVE ALL WARNINGS**: Keep critical warnings like "NEVER save audio files"
2. **MAINTAIN BONJOUR**: Keep self-announcement for backward compatibility
3. **USE ./go.py**: Always test through go.py, never direct Python
4. **DOCUMENT WHILE CODING**: Update docs as you convert
5. **NATURAL LANGUAGE**: Objects should understand intent, not rigid syntax

## 🎯 Conversion Pattern

```python
# Step 1: Inherit from UniversalPolymorphic
class MyService(UniversalPolymorphic):
    
    # Step 2: Override _handle_ask for queries
    def _handle_ask(self, question, **kwargs):
        q = str(question).lower()
        if 'status' in q:
            return self.status
        return super()._handle_ask(question, **kwargs)
    
    # Step 3: Override _handle_tell for formatting
    def _handle_tell(self, format, **kwargs):
        if format == 'json':
            return self.to_json()
        return super()._handle_tell(format, **kwargs)
    
    # Step 4: Override _handle_do for actions
    def _handle_do(self, action, **kwargs):
        if 'start' in action:
            return self.start()
        return super()._handle_do(action, **kwargs)
```

## 🚀 Benefits When Complete

1. **Simplicity**: 3 methods instead of 237+
2. **Consistency**: Same interface everywhere
3. **Discoverability**: `obj.ask("capabilities")`
4. **Natural Language**: `service.ask("are you running")`
5. **Self-Documenting**: Objects explain themselves
6. **Polymorphic**: Everything works with everything

## 📝 Notes

- Each conversion should result in FEWER lines of code
- Each conversion should be MORE intuitive to use
- Keep backward compatibility where needed
- Test each conversion thoroughly
- Commit after each successful conversion

## 🎉 The Vision

When complete, the ENTIRE codebase will use just 3 methods. No more hunting through documentation to find method names. No more wondering what a service can do. Just ask it!

```python
# The future is polymorphic!
anything.ask("what can you do")
anything.tell("explain yourself")
anything.do("whatever needs doing")
```

---

*This is the ultimate simplification - from 237 methods to just 3!*