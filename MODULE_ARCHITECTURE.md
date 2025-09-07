# Module Architecture

## Entry Point
- **go.py** - Single entry point that only starts services via subprocess. NO business logic.

## Core Infrastructure (polymorphic_core/)
Generic polymorphic patterns that have nothing to do with tournaments:

### Base Infrastructure
- **polymorphic_core/events.py** (was capability_announcer.py) - Event system that handles sync/async polymorphically
- **polymorphic_core/discovery.py** - Service discovery pattern (like Bonjour/mDNS)
- **polymorphic_core/async.py** - Provides async capabilities to any service
- **polymorphic_core/model.py** - Base polymorphic model pattern (ask/tell/do)
- **polymorphic_core/inputs.py** - Polymorphic input handling
- **polymorphic_core/storage.py** - Polymorphic storage pattern

### Audio Subsystem (polymorphic_core/audio/)
- **audio_player.py** - Plays audio polymorphically through any output
- **audio_provider.py** - Provides audio from any source
- **audio_request.py** - Handles audio requests polymorphically
- **opus_decoder.py** - Decodes Opus audio (Discord voice format)
- **transcription.py** - Transcribes audio to text (Whisper)
- **tts_service.py** - Text-to-speech service

## Tournament-Specific Modules

### Discord Integration
- **bonjour_discord.py** - Minimal Discord bot that announces messages via Bonjour
- **transcription_to_claude_bridge.py** - Bridges voice transcriptions to Claude

### Tournament Core
- **tournament_models.py** - SQLAlchemy models with 200+ methods
- **tournament_tracker.py** - Main tournament tracking logic
- **database_service.py** - Database operations and management
- **database_singleton.py** - Singleton database pattern

### Polymorphic Tournament Services
- **polymorphic_queries.py** - Natural language database queries
- **polymorphic_tabulator.py** - Data tabulation and formatting
- **polymorphic_image_generator.py** - Tournament visualizations

### Sync and Import
- **sync_service.py** - Syncs data from start.gg API
- **startgg_service.py** - start.gg API integration
- **startgg_sync.py** - Sync logic for start.gg

### Web Services
- **editor_service.py** - Web editor for organizations/contacts
- **claude_service.py** - Claude AI integration service
- **claude_cli_service.py** - Claude CLI integration (uses 'claude' command)

### Utilities
- **event_standardizer.py** - Standardizes tournament event names
- **normalize_events.py** - Event normalization logic
- **tournament_heatmap.py** - Generates heat maps
- **tournament_report.py** - Console reports
- **visualizer.py** - Data visualizations

## Import Flow

1. **go.py** starts services via subprocess (no imports)
2. **Services** (e.g., bonjour_discord.py) import:
   - Standard library modules
   - polymorphic_core components (via compatibility shims)
   - Domain-specific modules as needed

## Compatibility Shims
To maintain backward compatibility while refactoring:
- **capability_announcer.py** → redirects to polymorphic_core/events.py
- **capability_discovery.py** → redirects to polymorphic_core/discovery.py

## Key Principles

1. **go.py is just a starter** - NO logic, just subprocess.run()
2. **Polymorphic core is generic** - No tournament-specific code
3. **Services announce via Bonjour** - Self-discovery at runtime
4. **Everything is polymorphic** - Objects figure out intent
5. **Discord is just a conduit** - Minimal code, just message forwarding

## Module Dependencies

```
go.py
  ├── bonjour_discord.py
  │   ├── polymorphic_core/events (announcer)
  │   ├── polymorphic_core/discovery
  │   ├── polymorphic_core/audio/*
  │   └── transcription_to_claude_bridge.py
  │
  ├── editor_service.py
  │   ├── database_service.py
  │   └── tournament_models.py
  │
  ├── claude_service.py
  │   └── claude_cli_service.py
  │
  └── sync_service.py
      ├── startgg_service.py
      └── database_service.py
```

## Async/Sync Handling

The system handles async/sync polymorphically:
- **Events flow without blocking** - announcer detects context
- **Discord maintains heartbeat** - async operations don't block
- **Services can be sync or async** - polymorphic core adapts

## Voice Flow

1. Discord voice audio → opus_decoder → transcription
2. Transcription announced via Bonjour
3. transcription_to_claude_bridge hears announcement
4. Bridge calls Claude (in thread to not block)
5. Response → TTS → audio_player → Discord voice

All components communicate via announcements, not direct calls.