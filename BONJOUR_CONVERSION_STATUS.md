# Bonjour Services - Polymorphic Conversion Status

## 🔍 Analysis of Bonjour Services

### Services Found (8 main services):

1. **BonjourDiscord** (`bonjour_discord.py`)
   - **Current**: Has methods like `auto_join_voice()`, `register_handler()`, `run()`
   - **Needs Conversion**: ✅ YES
   - **Priority**: HIGH (core communication)

2. **BonjourMonitor** (`utils/bonjour_monitor.py`)
   - **Current**: Has methods like `start_live_monitor()`, `get_stats()`, `show_summary()`
   - **Needs Conversion**: ✅ YES
   - **Priority**: MEDIUM (debugging tool)

3. **BonjourAudioMixer** (`experimental/audio/bonjour_audio_mixer.py`)
   - **Current**: Has methods like `start_continuous_music()`, `mix_realtime()`, `get_mixed_stream()`
   - **Needs Conversion**: ✅ YES
   - **Priority**: HIGH (active service)

4. **DynamicCommandDiscovery** (`utils/bonjour_discovery_service.py`)
   - **Current**: Has methods like `list_commands()`, `show_dynamic_help()`, `route_command()`
   - **Needs Conversion**: ✅ YES
   - **Priority**: HIGH (command routing)

5. **BonjourTwilio** (`experimental/telephony/bonjour_twilio.py`)
   - **Current**: Has methods like `make_call()`, `handle_inbound()`, `transcribe_audio()`
   - **Needs Conversion**: ✅ YES
   - **Priority**: HIGH (telephony)

6. **BonjourDatabase** (`utils/bonjour_database.py`)
   - **Current**: Database wrapper with query methods
   - **Needs Conversion**: ✅ YES
   - **Priority**: MEDIUM

7. **BonjourMixin** (`utils/bonjour_mixin.py`)
   - **Current**: Mixin for models to announce themselves
   - **Needs Conversion**: ⚠️ PARTIAL (keep as mixin, but add ask/tell/do)
   - **Priority**: LOW

8. **BonjourAudioDetector** (`experimental/audio/bonjour_audio_detector.py`)
   - **Current**: Audio detection service
   - **Needs Conversion**: ✅ YES
   - **Priority**: LOW

## 🎯 Conversion Pattern for Bonjour Services

### Before (Current Pattern):
```python
class BonjourService:
    def __init__(self):
        announcer.announce("ServiceName", capabilities)
    
    def specific_method_1(self):
        # Do something specific
    
    def specific_method_2(self):
        # Do something else
    
    def another_method(self):
        # Yet another specific thing
```

### After (Polymorphic Pattern):
```python
from universal_polymorphic import UniversalPolymorphic

class BonjourService(UniversalPolymorphic):
    def __init__(self):
        super().__init__()  # Handles announcement
        
    def _handle_ask(self, question, **kwargs):
        # Parse natural language questions
        if 'status' in question:
            return self.status
        if 'capabilities' in question:
            return self.capabilities
            
    def _handle_tell(self, format, **kwargs):
        # Format output
        if format == 'json':
            return self.to_json()
        if format == 'discord':
            return self.format_for_discord()
            
    def _handle_do(self, action, **kwargs):
        # Perform actions
        if 'start' in action:
            return self.start_service()
        if 'announce' in action:
            return self.announce_capabilities()
```

## 📊 Summary

**Total Bonjour Services**: 8
**Need Full Conversion**: 7
**Need Partial Conversion**: 1

### Conversion Priority Order:
1. **BonjourDiscord** - Core communication
2. **BonjourAudioMixer** - Active audio service  
3. **BonjourTwilio** - Telephony integration
4. **DynamicCommandDiscovery** - Command routing
5. **BonjourMonitor** - Debugging tool
6. **BonjourDatabase** - Database wrapper
7. **BonjourAudioDetector** - Audio detection
8. **BonjourMixin** - Keep as mixin, enhance

## 🚀 Benefits After Conversion

1. **Consistency**: All Bonjour services use same 3 methods
2. **Self-Discovery**: Services can ask each other about capabilities
3. **Natural Language**: `service.ask("are you running")` instead of `service.is_running()`
4. **Simplified Integration**: Any service can interact with any other using ask/tell/do
5. **Automatic Documentation**: Services can tell their capabilities

## Example Usage After Conversion:

```python
# OLD WAY:
discord.auto_join_voice()
discord.register_handler(handler)
mixer.start_continuous_music()
monitor.get_stats()

# NEW WAY:
discord.do("join voice")
discord.do("register", handler=handler)
mixer.do("start music")
monitor.ask("stats")

# Services can discover each other:
discord.ask("capabilities")  # Returns what Discord can do
mixer.tell("status")         # Returns mixer status
monitor.tell("json")         # Returns monitor data as JSON
```