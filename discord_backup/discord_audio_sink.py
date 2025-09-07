#!/usr/bin/env python3
"""
discord_audio_sink.py - Custom audio sink for Discord voice receiving
Captures audio from Discord voice channels and announces via Bonjour
"""

import discord
import wave
import io
from datetime import datetime
from typing import Dict, Optional
from capability_announcer import announcer
from capability_discovery import register_capability, discover_capability

class PolymorphicAudioSink:
    """Audio sink that captures Discord voice data polymorphically"""
    
    def __init__(self):
        """Initialize the audio sink"""
        self.audio_data: Dict[int, io.BytesIO] = {}  # user_id -> audio buffer
        self.finished_callback = None
        self.guild_id = None
        
        # Announce ourselves
        announcer.announce(
            "PolymorphicAudioSink",
            [
                "I capture audio from Discord voice channels",
                "I store audio polymorphically",
                "I announce when audio is received",
                "I work with any audio format"
            ]
        )
    
    def write(self, data: bytes, user_id: int):
        """Called when audio data is received from a user"""
        print(f"📝 [DEBUG] Audio received: {len(data)} bytes from user {user_id}")
        
        if user_id not in self.audio_data:
            self.audio_data[user_id] = io.BytesIO()
            print(f"📝 [DEBUG] New user {user_id} started speaking")
            announcer.announce(
                "AUDIO_CAPTURE_START",
                [
                    f"Started capturing audio from user {user_id}",
                    f"Guild: {self.guild_id}"
                ]
            )
        
        # Write audio data to buffer
        self.audio_data[user_id].write(data)
        
        # Announce audio received
        announcer.announce(
            "AUDIO_DATA_RECEIVED",
            [
                f"USER: {user_id}",
                f"BYTES: {len(data)}",
                f"TOTAL: {self.audio_data[user_id].tell()} bytes"
            ]
        )
    
    def cleanup(self):
        """Called when recording stops"""
        announcer.announce(
            "AUDIO_CAPTURE_COMPLETE",
            [
                f"Captured audio from {len(self.audio_data)} users",
                "Processing audio data..."
            ]
        )
        
        # Store each user's audio polymorphically
        storage = discover_capability('storage')
        if storage:
            for user_id, audio_buffer in self.audio_data.items():
                audio_data = audio_buffer.getvalue()
                if len(audio_data) > 0:
                    # Store in polymorphic storage
                    storage_id = storage.accept_audio(
                        audio_data,
                        user_id,
                        self.guild_id or 0
                    )
                    
                    announcer.announce(
                        "AUDIO_STORED",
                        [
                            f"User {user_id} audio stored",
                            f"Storage ID: {storage_id}",
                            f"Size: {len(audio_data)} bytes"
                        ]
                    )
                    
                    # Trigger transcription/processing
                    self._process_audio(user_id, audio_data)
        
        # Clear buffers
        self.audio_data.clear()
        
        # Call finished callback if set
        if self.finished_callback:
            # Discover async service
            async_service = discover_capability('async')
            if async_service:
                async_service.create_task(self.finished_callback(self))
            else:
                # Fallback if async service not available
                announcer.announce("AudioSink", ["Async service not available for callback"])
    
    def _process_audio(self, user_id: int, audio_data: bytes):
        """Process captured audio"""
        announcer.announce(
            "AUDIO_PROCESSING",
            [
                f"Processing audio from user {user_id}",
                f"Size: {len(audio_data)} bytes",
                "Ready for transcription"
            ]
        )
        
        # Announce for transcription service
        announcer.announce(
            "TRANSCRIBE_REQUEST",
            [
                f"USER: {user_id}",
                f"AUDIO_SIZE: {len(audio_data)}",
                "TYPE: Discord voice"
            ]
        )
        
        # If we have Whisper, transcribe
        try:
            import subprocess
            import tempfile
            
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            # Try to transcribe with Whisper
            result = subprocess.run(
                ['whisper', temp_path, '--model', 'base', '--language', 'en', '--output_format', 'txt'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Read transcription
                with open(temp_path + '.txt', 'r') as f:
                    transcription = f.read().strip()
                
                announcer.announce(
                    "TRANSCRIPTION_COMPLETE",
                    [
                        f"USER {user_id} said: '{transcription}'",
                        "Processing through Claude..."
                    ]
                )
                
                # The announcement above is all we need!
                # Pure Bonjour services will hear TRANSCRIPTION_COMPLETE and process it
            
            # Cleanup
            import os
            os.remove(temp_path)
            if os.path.exists(temp_path + '.txt'):
                os.remove(temp_path + '.txt')
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            announcer.announce(
                "TRANSCRIPTION_UNAVAILABLE",
                [
                    "Whisper not available",
                    "Install with: pip install openai-whisper",
                    "Audio stored for later processing"
                ]
            )
        except Exception as e:
            announcer.announce(
                "TRANSCRIPTION_ERROR",
                [f"Error: {e}"]
            )
    
    # Removed _process_transcription - using pure Bonjour announcements instead!

class VoiceRecordingSink:
    """Audio sink for Discord voice recording"""
    
    def __init__(self):
        self.polymorphic_sink = PolymorphicAudioSink()
        self.audio_data = {}  # Compatibility with discord.py if needed
        
    def write(self, data: bytes, user):
        """Write audio data from a user"""
        user_id = user.id if hasattr(user, 'id') else user
        self.polymorphic_sink.write(data, user_id)
    
    def cleanup(self):
        """Called when recording stops"""
        self.polymorphic_sink.cleanup()

# Global sink instance
_audio_sink = None

def get_audio_sink(guild_id: int = None) -> VoiceRecordingSink:
    """Get or create audio sink for recording"""
    global _audio_sink
    if _audio_sink is None:
        _audio_sink = VoiceRecordingSink()
    
    if guild_id:
        _audio_sink.polymorphic_sink.guild_id = guild_id
    
    return _audio_sink

# Register with capability discovery
try:
    register_capability("audio_sink", lambda: get_audio_sink())
    announcer.announce("AudioSink", ["Registered as discoverable capability"])
except ImportError:
    pass