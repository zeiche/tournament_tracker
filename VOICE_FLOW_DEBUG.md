# Voice Process Flow - Complete Documentation & Debug Guide

## 🎯 Goal
When a user speaks "Can you hear me?" in Discord #general voice channel, Claude should respond with voice.

## 🚀 INITIALIZATION SEQUENCE

### Phase 1: Command Execution
```bash
./go.py --discord-bot --discord-mode voice
```

### Phase 2: Environment Setup (go.py)
1. **Set authorization**: `os.environ['GO_PY_AUTHORIZED'] = '1'`
2. **Load .env file**: Reads Discord token and other config
3. **Import services**: Based on mode='voice'

### Phase 3: Service Imports & Registration
When `discord_voice_bot.py` imports happen:
```python
# These imports trigger service initialization
import pure_bonjour_voice_bridge    # Creates bridge instance, registers listener
import polymorphic_tts_service       # Creates TTS instance, registers listener  
import polymorphic_audio_player      # Creates player instance, registers listener
```

Each service on import:
1. Creates singleton instance (`_instance` pattern)
2. Announces capabilities via Bonjour
3. Registers announcement listeners with `announcer.add_listener()`

### Phase 4: Discord Bot Initialization
```python
async def main():
    bot = ClaudeVoiceBot()           # Create bot instance
    await bot.start(token)           # Connect to Discord
```

### Phase 5: Discord Events
1. **on_ready()** event fires when connected
2. **auto_join_general_voice()** executes:
   - Searches for #general voice channel
   - Connects to voice channel
   - Gets VoiceBot cog
   - **CRITICAL**: Should call `start_recording()`
   - Attaches audio sink

### Phase 6: Audio Sink Setup
```python
await voice_cog.start_recording(guild_id):
    self.audio_sink = get_audio_sink(guild_id)    # Get sink instance
    self.voice_client.start_recording(            # Start Discord recording
        self.audio_sink,
        self.on_recording_finished
    )
```

### Phase 7: Service Ready State
All services now listening for announcements:
- **Bridge** → Waiting for `TRANSCRIPTION_COMPLETE`
- **TTS** → Waiting for `TEXT_TO_SPEECH`
- **Player** → Waiting for `AUDIO_READY`

## ⚠️ MISSING/BROKEN INITIALIZATION STEPS

### 1. ❌ Service Import Verification
**Problem**: Services might not be actually initializing
**Test**: Add print statements in each service's `__init__`

### 2. ❌ Listener Registration Verification  
**Problem**: Listeners might not be properly registered
**Test**: Print `len(announcer.listeners)` after all imports

### 3. ❌ Voice Client Recording Start
**Problem**: `start_recording()` might not be called
**Test**: Add print in `start_recording()` method

### 4. ❌ Audio Sink Registration
**Problem**: Sink might not be properly attached to voice client
**Test**: Verify `voice_client.sink` is not None

## 📋 Current Architecture Components

### 1. Entry Point
- **Command**: `./go.py --discord-bot --discord-mode voice`
- **What it does**: Starts the Discord voice bot with all Bonjour services
- **Current status**: ❓ UNCLEAR - May be starting wrong service

### 2. Discord Voice Bot (`discord_voice_bot.py`)
- **Purpose**: Connect to Discord, join voice channel, capture audio
- **Auto-join**: Should auto-join #general voice on startup
- **Recording**: Should auto-start recording when joining
- **Components**:
  - `ClaudeVoiceBot` class - Main bot
  - `VoiceBot` cog - Voice functionality
  - Audio sink attachment for recording

### 3. Audio Capture (`discord_audio_sink.py`)
- **Purpose**: Capture raw audio from Discord voice
- **Classes**:
  - `PolymorphicAudioSink` - Captures and stores audio
  - `VoiceRecordingSink` - Wrapper for Discord compatibility
- **On audio received**: 
  1. Stores audio in buffer
  2. When user stops speaking → Transcribes with Whisper
  3. Announces `TRANSCRIPTION_COMPLETE`

### 4. Pure Bonjour Voice Bridge (`pure_bonjour_voice_bridge.py`)
- **Listens for**: `TRANSCRIPTION_COMPLETE` announcements
- **Actions**:
  1. Extracts transcription text and user ID
  2. Calls `./go.py --ai-chat` with the text (via subprocess)
  3. Gets Claude's response
  4. Announces `CLAUDE_RESPONSE`
  5. Then announces `TEXT_TO_SPEECH`

### 5. TTS Service (`polymorphic_tts_service.py`)
- **Listens for**: `TEXT_TO_SPEECH` announcements
- **Actions**:
  1. Extracts text to convert
  2. Generates .wav file using espeak
  3. Announces `AUDIO_READY` with file path

### 6. Audio Player (`polymorphic_audio_player.py`)
- **Listens for**: `AUDIO_READY` announcements
- **Actions**:
  1. Gets .wav file path
  2. Plays through Discord voice client
  3. Announces `AUDIO_PLAYED`

## 🔴 Current Issues & Breakpoints

### Issue 1: Wrong Service Starting?
- `./go.py --discord-bot` was starting `discord_service.py` not `discord_voice_bot.py`
- Fixed by checking mode='voice' in go.py
- **Status**: ✅ FIXED

### Issue 2: Discord Token
- Bot can't connect - "Invalid token" error
- Token is in .env but not loaded when run directly
- **Status**: ✅ FIXED (must use go.py)

### Issue 3: Audio Not Being Captured
- **UNKNOWN**: Is the audio sink actually receiving data?
- **UNKNOWN**: Is Discord.py's `start_recording()` working?
- **Debug needed**: Add logging to `write()` method in audio sink

### Issue 4: Whisper Transcription
- **UNKNOWN**: Is Whisper installed and working?
- **UNKNOWN**: Is audio format correct for Whisper?
- **Debug needed**: Check if whisper command exists

### Issue 5: Announcement Listeners
- Multiple services overriding `announcer.announce`
- Fixed with proper listener system
- **Status**: ✅ FIXED

### Issue 6: Claude Response Path
- Bridge calls `./go.py --ai-chat` via subprocess
- **UNKNOWN**: Is this working?
- **UNKNOWN**: Is response being parsed correctly?

## 🐛 Debug Steps

### Step 1: Verify Bot Connection
```bash
./go.py --discord-bot --discord-mode voice
# Should see:
# ✅ Bot is online!
# 🔍 Found voice channel: #general
# 🎤 Auto-joined #general
# 🔴 Started recording automatically
```

### Step 2: Check Audio Capture
Add debug output to `discord_audio_sink.py`:
```python
def write(self, data: bytes, user_id: int):
    print(f"📝 Audio received: {len(data)} bytes from user {user_id}")
```

### Step 3: Test Whisper
```bash
which whisper
whisper --help
```

### Step 4: Monitor Announcements
Add to each service:
```python
announcer.announce("SERVICE_NAME", [f"Debug: {action}"])
```

### Step 5: Test Claude Integration
```bash
echo "test message" | ./go.py --ai-chat
```

## 🔄 Expected Flow Trace

When user says "Can you hear me?":

1. **Discord** → Audio bytes received
2. **AudioSink.write()** → Buffer audio (should see debug output)
3. **AudioSink.cleanup()** → Process when user stops speaking
4. **Whisper** → Transcribe audio to text
5. **Announce** → `TRANSCRIPTION_COMPLETE: USER 123 said: 'Can you hear me?'`
6. **Bridge hears** → Processes transcription
7. **Bridge calls** → `./go.py --ai-chat` with text
8. **Claude responds** → "Yes, I can hear you!"
9. **Announce** → `CLAUDE_RESPONSE: Yes, I can hear you!`
10. **Announce** → `TEXT_TO_SPEECH: TEXT: Yes, I can hear you!`
11. **TTS hears** → Generates .wav file
12. **Announce** → `AUDIO_READY: FILE: /tmp/xyz.wav`
13. **Player hears** → Plays through Discord
14. **User hears** → Claude's voice response

## 🚨 Critical Requirements

1. **Whisper** must be installed: `pip install openai-whisper`
2. **FFmpeg** must be installed: `sudo apt install ffmpeg`
3. **espeak** must be installed: `sudo apt install espeak`
4. **Discord token** must be valid in .env
5. **Bot** must have voice permissions in Discord
6. **Services** must all be imported to register listeners

## 📝 Testing Each Component

### Test 1: Audio Sink
```python
# In discord_audio_sink.py, add:
print("SINK IMPORTED AND READY")
```

### Test 2: Announcement System
```python
# Test announcement flow
from capability_announcer import announcer
announcer.announce("TRANSCRIPTION_COMPLETE", ["USER 123 said: 'test'"])
# Should trigger the bridge
```

### Test 3: Voice Response
```python
# Test TTS directly
from polymorphic_tts_service import tts_service
tts_service.generate_audio("Hello world", "normal")
```

## ❌ What's NOT Working

Based on "Can you hear me?" getting no response:

1. **Most likely**: Audio sink not receiving/processing audio
2. **Or**: Whisper transcription failing silently  
3. **Or**: Announcements not being heard by services
4. **Or**: Claude integration broken
5. **Or**: TTS/playback failing

## 🔧 Next Debugging Steps

1. Add verbose logging to EVERY step
2. Test each component in isolation
3. Monitor announcement flow
4. Check system dependencies (whisper, ffmpeg, espeak)
5. Verify Discord permissions and connection