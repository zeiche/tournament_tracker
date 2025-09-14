#!/usr/bin/env python3
"""
polymorphic_audio_request.py - Service that announces it needs audio
Any service that HAS audio can respond to these announcements
Pure Bonjour - no direct dependencies!
"""

from polymorphic_core.local_bonjour import local_announcer
from polymorphic_core import register_capability
import time
from typing import Optional, Callable

class PolymorphicAudioRequest:
    """Service that requests audio through announcements"""
    
    _instance = None
    _listeners = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce what we need
        local_announcer.announce(
            "PolymorphicAudioRequest",
            [
                "I NEED audio data",
                "I listen for AUDIO_AVAILABLE announcements",
                "I don't care WHERE audio comes from",
                "I process any audio that's announced",
                "Services with audio should announce AUDIO_AVAILABLE",
                "I am the universal audio consumer"
            ]
        )
        
        self.audio_handlers = []
        self.request_audio_continuously()
    
    def request_audio_continuously(self):
        """Continuously announce that we want audio"""
        local_announcer.announce(
            "AUDIO_REQUEST",
            [
                "REQUESTING: Audio data from ANY source",
                "FORMATS: wav, pcm, mp3, anything",
                "PURPOSE: Transcription and processing",
                "RESPOND: Announce AUDIO_AVAILABLE with your data"
            ]
        )
    
    def on_audio_available(self, source: str, audio_data: bytes, metadata: dict):
        """Called when ANY service announces audio is available"""
        local_announcer.announce(
            "AUDIO_RECEIVED",
            [
                f"Received audio from: {source}",
                f"Size: {len(audio_data)} bytes",
                "Processing..."
            ]
        )
        
        # Process the audio
        for handler in self.audio_handlers:
            try:
                handler(source, audio_data, metadata)
            except Exception as e:
                local_announcer.announce("AudioRequest", [f"Handler error: {e}"])
    
    def register_audio_handler(self, handler: Callable):
        """Register a handler for when audio arrives"""
        self.audio_handlers.append(handler)
        local_announcer.announce(
            "AudioRequest",
            [f"New audio handler registered. Total: {len(self.audio_handlers)}"]
        )
    
    def request_specific_audio(self, source_type: str):
        """Request audio from a specific type of source"""
        local_announcer.announce(
            "TARGETED_AUDIO_REQUEST",
            [
                f"REQUESTING: Audio from {source_type}",
                f"PRIORITY: High",
                "RESPOND: If you are {source_type}, please provide audio"
            ]
        )

# Global instance
_audio_requester = PolymorphicAudioRequest()

def get_audio_requester():
    """Get the global audio requester"""
    return _audio_requester

# Register with capability discovery
try:
    register_capability("audio_request", get_audio_requester)
    local_announcer.announce("PolymorphicAudioRequest", ["Registered as discoverable capability"])
except ImportError:
    pass

# Listen for audio announcements
def listen_for_audio():
    """This would subscribe to AUDIO_AVAILABLE announcements"""
    # In a real implementation, this would use an event system
    # For now, services will call on_audio_available directly
    pass