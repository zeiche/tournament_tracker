#!/usr/bin/env python3
"""
polymorphic_audio_provider.py - Provides audio when requested
Listens for AUDIO_REQUEST announcements and responds with audio
Could be Discord, microphone, file, or ANY audio source
"""

from polymorphic_core.local_bonjour import local_announcer
from polymorphic_core import register_capability, discover_capability
import os
from typing import Optional

class PolymorphicAudioProvider:
    """Service that provides audio when requested"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce what we can provide
        local_announcer.announce(
            "PolymorphicAudioProvider",
            [
                "I HAVE audio data",
                "I listen for AUDIO_REQUEST announcements",
                "I respond with AUDIO_AVAILABLE",
                "I can provide Discord voice audio",
                "I can provide microphone audio",
                "I can provide file audio",
                "I am polymorphic - I provide what I have"
            ]
        )
        
        self.audio_buffer = {}
        self.listen_for_requests()
    
    def listen_for_requests(self):
        """Listen for audio requests and respond"""
        # When we see AUDIO_REQUEST, we check if we have audio
        # This would be triggered by announcement system
        pass
    
    def provide_discord_audio(self, user_id: int, audio_data: bytes):
        """Provide audio from Discord"""
        local_announcer.announce(
            "AUDIO_AVAILABLE",
            [
                "SOURCE: Discord voice",
                f"USER: {user_id}",
                f"SIZE: {len(audio_data)} bytes",
                "TYPE: PCM audio",
                "READY: For transcription"
            ]
        )
        
        # Notify audio requester
        audio_requester = discover_capability('audio_request')
        if audio_requester:
            audio_requester.on_audio_available(
                f"discord_user_{user_id}",
                audio_data,
                {"type": "discord_voice", "user_id": user_id}
            )
    
    def provide_file_audio(self, file_path: str):
        """Provide audio from a file"""
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            local_announcer.announce(
                "AUDIO_AVAILABLE",
                [
                    "SOURCE: File system",
                    f"FILE: {file_path}",
                    f"SIZE: {len(audio_data)} bytes",
                    "READY: For processing"
                ]
            )
            
            # Notify audio requester
            audio_requester = discover_capability('audio_request')
            if audio_requester:
                audio_requester.on_audio_available(
                    f"file_{os.path.basename(file_path)}",
                    audio_data,
                    {"type": "file", "path": file_path}
                )
    
    def provide_simulated_audio(self, text: str):
        """Provide simulated audio (text as if it were speech)"""
        local_announcer.announce(
            "AUDIO_AVAILABLE",
            [
                "SOURCE: Simulated voice",
                f"TEXT: '{text}'",
                "TYPE: Text simulation",
                "READY: For processing"
            ]
        )
        
        # Notify audio requester
        audio_requester = discover_capability('audio_request')
        if audio_requester:
            audio_requester.on_audio_available(
                "simulated_voice",
                text.encode(),
                {"type": "simulated", "text": text}
            )
    
    def buffer_audio(self, source: str, audio_data: bytes):
        """Buffer audio for later provision"""
        self.audio_buffer[source] = audio_data
        local_announcer.announce(
            "AUDIO_BUFFERED",
            [
                f"Buffered audio from: {source}",
                f"Size: {len(audio_data)} bytes",
                f"Total sources: {len(self.audio_buffer)}"
            ]
        )
    
    def provide_buffered_audio(self):
        """Provide all buffered audio"""
        for source, audio_data in self.audio_buffer.items():
            local_announcer.announce(
                "AUDIO_AVAILABLE",
                [
                    f"SOURCE: {source} (buffered)",
                    f"SIZE: {len(audio_data)} bytes"
                ]
            )
            
            audio_requester = discover_capability('audio_request')
            if audio_requester:
                audio_requester.on_audio_available(
                    source,
                    audio_data,
                    {"type": "buffered", "source": source}
                )
        
        # Clear buffer after providing
        self.audio_buffer.clear()

# Global instance
_audio_provider = PolymorphicAudioProvider()

def get_audio_provider():
    """Get the global audio provider"""
    return _audio_provider

# Register with capability discovery
try:
    register_capability("audio_provider", get_audio_provider)
    local_announcer.announce("PolymorphicAudioProvider", ["Registered as discoverable capability"])
except ImportError:
    pass