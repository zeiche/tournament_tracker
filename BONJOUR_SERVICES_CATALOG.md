# Bonjour Services Catalog - Tournament Tracker
## Complete Documentation of Self-Announcing Services
### Generated: January 8, 2025

---

## Table of Contents
1. [Overview](#overview)
2. [Core Infrastructure](#core-infrastructure)
3. [Service Catalog](#service-catalog)
4. [Announcement Patterns](#announcement-patterns)
5. [Event Flow](#event-flow)
6. [Discovery API](#discovery-api)
7. [Implementation Status](#implementation-status)

---

## Overview

The Tournament Tracker implements a Bonjour-style service discovery system where every component self-announces its presence and capabilities. This creates a zero-configuration, self-documenting system that Claude and other services can discover dynamically at runtime.

### Key Philosophy
- **Self-Announcing**: Services broadcast what they can do when they start
- **Dynamic Discovery**: No hardcoded dependencies or static configuration
- **Polymorphic Design**: Works seamlessly with sync/async code
- **Living Documentation**: System describes itself through real-time announcements

---

## Core Infrastructure

### 1. Event System (`polymorphic_core/events.py`)
```python
class SynchronousEvents:
    - announce(service_name, capabilities, examples)
    - add_listener(listener_func)
    - get_announcements_for_claude()
```

**Features:**
- Global singleton `announcer` instance
- Polymorphic sync/async handling
- Event listener pattern for real-time updates
- Context generation for Claude

### 2. Discovery Registry (`polymorphic_core/discovery.py`)
```python
class CapabilityRegistry:
    - register_model(model_class)
    - register_function(func, category)
    - register_service(service_name, service_getter)
    - discover_all_capabilities()
```

**Features:**
- Model introspection and capability extraction
- Service registration and lookup
- Dynamic context generation
- Auto-discovery of tournament models

### 3. Announcer Bridge (`capability_announcer.py`)
Compatibility layer that:
- Announces tournament models (Tournament, Player, Organization)
- Announces query engine capabilities
- Generates full context for Claude
- Provides backward compatibility

---

## Service Catalog

### Discord Services

#### 1. **BonjourDiscord** (`bonjour_discord.py`)
**Announces:**
- "I connect to Discord"
- "I receive messages and announce them"
- "Register handlers with me to process messages"
- "I don't do business logic - I just forward messages"

**Events:**
- `DISCORD_READY` - When connected
- `DISCORD_MESSAGE` - When message received
- `DISCORD_VOICE_JOINED` - When joining voice channel

#### 2. **Voice Services** (Discord Voice)
- **PolymorphicAudioPlayer**: Plays audio through Discord
- **PolymorphicTTSService**: Text-to-speech generation
- **PolymorphicTranscription**: Voice-to-text conversion

### Web Services

#### 3. **EditorService** (`editor_service.py`)
**Announces:**
- "I provide web-based tournament editing"
- "I run on port 8081"
- "I handle organization management"
- "I support graceful shutdown"

**Features:**
- Organization name editing
- Contact management
- Tournament assignment
- Merge operations

### Telephony Services

#### 4. **BonjourTwilio** (`bonjour_twilio.py`)
**Announces:**
- "I handle phone calls and SMS"
- "I bridge voice to Claude"
- "I provide tournament info via phone"

**Events:**
- `TWILIO_CALL_INCOMING` - Inbound call
- `TWILIO_SMS_RECEIVED` - SMS message
- `TWILIO_CALL_STATUS` - Call state changes

#### 5. **InboundCallHandler** (`inbound_call_handler.py`)
**Announces:**
- "I answer tournament questions via phone"
- "I use Claude for natural language"
- "I provide TTS responses"

#### 6. **TwilioClaudeHandler** (`twilio_claude_handler.py`)
**Announces:**
- "I bridge Twilio calls to Claude"
- "I handle voice transcription"
- "I generate spoken responses"

### Audio Services

#### 7. **PolymorphicAudioPlayer** (`polymorphic_core/audio/audio_player.py`)
**Announces:**
- "I play ANY audio that's announced as ready"
- "I listen for AUDIO_READY announcements"
- "I play through Discord voice channels"
- "I clean up files after playback"

**Events:**
- `AUDIO_PLAYING` - Starting playback
- `AUDIO_PLAYED` - Playback complete
- `AUDIO_DISCORD` - Playing via Discord
- `AUDIO_CLEANUP` - File cleaned up

#### 8. **PolymorphicTTSService** (`polymorphic_core/audio/tts_service.py`)
**Announces:**
- "I convert text to speech"
- "I generate audio files"
- "I support multiple voices"

**Events:**
- `TTS_REQUEST` - Generation requested
- `AUDIO_READY` - Audio file ready
- `TTS_ERROR` - Generation failed

#### 9. **PolymorphicTranscription** (`polymorphic_core/audio/transcription.py`)
**Announces:**
- "I transcribe audio to text"
- "I handle Opus decoding"
- "I support real-time transcription"

**Events:**
- `TRANSCRIPTION_START` - Starting transcription
- `TRANSCRIPTION_COMPLETE` - Text ready
- `TRANSCRIPTION_ERROR` - Failed to transcribe

### Data Services

#### 10. **Tournament Model** (`tournament_models.py`)
**Announces:**
- "Track tournament events with dates and locations"
- "Calculate attendance and growth metrics"
- "Determine if tournaments are majors"
- "Measure days since tournament"

**Examples:**
- "Ask about recent tournaments"
- "Get tournament attendance numbers"
- "Find tournaments by venue"

#### 11. **Player Model** (`tournament_models.py`)
**Announces:**
- "Track player performance and standings"
- "Calculate win rates and consistency scores"
- "Show podium finishes"
- "Rank players by points"

**Examples:**
- "Show top players"
- "Get player statistics"
- "Find player's tournament history"

#### 12. **Organization Model** (`tournament_models.py`)
**Announces:**
- "Track tournament organizers and venues"
- "Count total events hosted"
- "Manage contact information"
- "Show organization growth"

**Examples:**
- "Which venues host the most events"
- "Organization contact details"
- "Venue tournament history"

### Query Services

#### 13. **Query Engine** (`polymorphic_queries.py`)
**Announces:**
- "Natural language tournament queries"
- "Top player rankings"
- "Recent tournament listings"
- "Organization statistics"

**Examples:**
- "show top 10 players"
- "recent tournaments"
- "show player WEST"

### AI Services

#### 14. **ClaudeService** (`claude_service.py`)
**Announces:**
- "I provide Claude AI integration"
- "I answer tournament questions"
- "I format responses for Discord"

#### 15. **PolymorphicClaudeVoice** (`polymorphic_claude_voice.py`)
**Announces:**
- "Claude's polymorphic tournament intelligence"
- "I answer questions about tournaments and players"
- "I work via voice or text - doesn't matter to me"
- "Just ask naturally - I figure out what you want"

**Events:**
- `CLAUDE_THINKING` - Processing query
- `CLAUDE_RESPONSE` - Answer ready
- `CLAUDE_ERROR` - Query failed

### Utility Services

#### 16. **ShutdownCoordinator** (`shutdown_coordinator.py`)
**Announces:**
- "I coordinate graceful shutdowns"
- "I notify all services of shutdown"
- "I ensure clean termination"

#### 17. **ProcessGuard** (`go_py_guard.py`)
**Announces:**
- "I ensure services start via go.py"
- "I prevent direct script execution"
- "I maintain process integrity"

---

## Announcement Patterns

### Service Initialization Pattern
```python
class MyService:
    def __init__(self):
        announcer.announce(
            "MyService",
            [
                "What I can do",
                "My capabilities",
                "My features"
            ],
            examples=["How to use me"]
        )
```

### Event Broadcasting Pattern
```python
# When something happens
announcer.announce(
    "EVENT_TYPE",
    [
        f"Detail 1: {value}",
        f"Detail 2: {value}",
        f"Status: {status}"
    ]
)
```

### State Change Pattern
```python
# When state changes
announcer.announce(
    "SERVICE_STATE",
    [f"New state: {state}", f"Reason: {reason}"]
)
```

### Error Announcement Pattern
```python
try:
    # operation
except Exception as e:
    announcer.announce(
        "SERVICE_ERROR",
        [f"Operation failed: {e}"]
    )
```

---

## Event Flow

### Typical Message Flow
```
1. User sends Discord message
   ↓
2. BonjourDiscord announces: DISCORD_MESSAGE
   ↓
3. ClaudeService picks up announcement
   ↓
4. ClaudeService announces: CLAUDE_THINKING
   ↓
5. Query Engine announces: QUERY_PROCESSING
   ↓
6. Database announces: DATA_RETRIEVED
   ↓
7. ClaudeService announces: CLAUDE_RESPONSE
   ↓
8. Discord sends response to user
```

### Voice Call Flow
```
1. Phone call arrives
   ↓
2. BonjourTwilio announces: TWILIO_CALL_INCOMING
   ↓
3. InboundCallHandler announces: HANDLING_CALL
   ↓
4. Transcription announces: TRANSCRIPTION_START
   ↓
5. ClaudeVoice announces: PROCESSING_VOICE_QUERY
   ↓
6. TTS announces: GENERATING_SPEECH
   ↓
7. AudioPlayer announces: AUDIO_READY
   ↓
8. Twilio plays response to caller
```

---

## Discovery API

### For Services

#### Register a Service
```python
from polymorphic_core import register_capability

def get_my_service():
    return MyService.instance()

register_capability("my_service", get_my_service)
```

#### Discover a Service
```python
from polymorphic_core import discover_capability

service = discover_capability("discord_bot")
if service:
    await service.send_message("Hello!")
```

#### List All Services
```python
from polymorphic_core import list_capabilities

available = list_capabilities()
print(f"Services: {available['services']}")
print(f"Models: {available['models']}")
```

### For Claude

#### Get Full Context
```python
from capability_announcer import get_full_context

context = get_full_context()
# Returns formatted string with all announcements
```

#### Listen for Announcements
```python
from polymorphic_core import announcer

def on_announcement(service, capabilities, examples):
    print(f"{service} can: {capabilities}")

announcer.add_listener(on_announcement)
```

---

## Implementation Status

### ✅ Fully Implemented
- Core announcement infrastructure
- Discord service announcements
- Audio service announcements
- Twilio/telephony announcements
- Model capability announcements
- Query engine announcements
- Editor service announcements
- Shutdown coordination

### 🚧 Partially Implemented
- Database operation announcements
- File I/O announcements
- Web service endpoint announcements
- Error recovery announcements

### 📋 Planned
- Metrics/monitoring announcements
- Performance announcements
- Cache state announcements
- Configuration change announcements
- Security event announcements

---

## Usage Examples

### Starting a Service
```bash
# Services self-announce on startup
./go.py --discord-bot
# BonjourDiscord announces its capabilities

./go.py --edit-contacts  
# EditorService announces web UI availability

./go.py --twilio-bridge
# BonjourTwilio announces telephony ready
```

### Discovering Services Programmatically
```python
# In any Python code
from polymorphic_core import discover_capability

# Find Discord bot
discord = discover_capability("discord_bot")

# Find audio player
audio = discover_capability("audio_player")

# Find Claude service
claude = discover_capability("claude")
```

### Adding New Service
```python
from polymorphic_core import announcer, register_capability

class NewService:
    def __init__(self):
        # Announce what you can do
        announcer.announce(
            "NewService",
            ["My capabilities here"]
        )
        
        # Register for discovery
        register_capability("new_service", lambda: self)
    
    def do_something(self):
        # Announce what you're doing
        announcer.announce(
            "NEW_SERVICE_ACTION",
            ["Doing something"]
        )
```

---

## Benefits

1. **Zero Configuration**: Services find each other automatically
2. **Self-Documenting**: System explains itself via announcements
3. **Dynamic Adaptation**: Services can appear/disappear at runtime
4. **Debugging Paradise**: See exactly what's happening in real-time
5. **Polymorphic Design**: Works with any code style (sync/async/callback)
6. **Extensible**: Easy to add new services that integrate immediately

---

## Best Practices

1. **Always Announce on Init**: Every service should announce when created
2. **Announce State Changes**: Let others know when your state changes
3. **Announce Errors**: Even failures should be announced
4. **Use Descriptive Names**: Make announcement types clear and specific
5. **Include Context**: Provide useful details in announcements
6. **Register for Discovery**: Make your service discoverable by others
7. **Listen Selectively**: Only listen for announcements you care about

---

## Troubleshooting

### Service Not Announcing
- Check that service imports `announcer`
- Verify announcement happens in `__init__`
- Ensure service is started via `go.py`

### Announcements Not Received
- Check listener is registered before announcement
- Verify no exceptions in listener function
- Ensure async context handling is correct

### Discovery Not Working
- Verify service registered with `register_capability`
- Check service name matches exactly
- Ensure service is running

---

## Future Enhancements

1. **Announcement Filtering**: Subscribe to specific event types
2. **Announcement History**: Replay past announcements
3. **Remote Discovery**: Discover services across network
4. **Health Monitoring**: Services announce health status
5. **Load Balancing**: Discover least-loaded service instance
6. **Service Mesh**: Full microservice discovery mesh

---

This Bonjour-style discovery system transforms the Tournament Tracker into a self-aware, self-documenting ecosystem where services collaborate through dynamic discovery rather than static configuration.