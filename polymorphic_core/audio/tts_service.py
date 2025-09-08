#!/usr/bin/env python3
"""
polymorphic_tts_service.py - Pure Bonjour TTS Service
Listens for TEXT_TO_SPEECH announcements and converts text to audio
Announces AUDIO_READY when complete
"""

import subprocess
import tempfile
import os
from typing import Dict, Any
from polymorphic_core import announcer
from polymorphic_core import register_capability

class PolymorphicTTSService:
    """Pure Bonjour TTS service - listens and announces"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        print("🔊 [DEBUG] PolymorphicTTSService initializing...")
        
        # Announce our capabilities
        announcer.announce(
            "PolymorphicTTSService",
            [
                "I convert ANY text to speech",
                "I listen for TEXT_TO_SPEECH announcements",
                "I support multiple voices: normal, robot, excited, etc.",
                "I announce AUDIO_READY when TTS is complete",
                "I use espeak, festival, or any TTS engine",
                "I am voice-agnostic and polymorphic"
            ]
        )
        
        self.audio_cache = {}
        self.start_listening()
    
    def start_listening(self):
        """Hook into announcements to listen for TEXT_TO_SPEECH"""
        def announcement_listener(service_name: str, capabilities: list, examples: list = None):
            # Listen for TEXT_TO_SPEECH announcements
            if service_name == "TEXT_TO_SPEECH":
                self.on_tts_request(capabilities)
        
        # Register as a listener
        announcer.add_listener(announcement_listener)
        print(f"🔊 [DEBUG] TTS registered listener. Total listeners: {len(announcer.listeners)}")
        announcer.announce("PolymorphicTTSService", ["Now listening for TEXT_TO_SPEECH announcements"])
    
    def on_tts_request(self, request_data: list):
        """Process TTS request from announcement"""
        text = None
        voice_type = "normal"
        request_id = "unknown"
        
        # Parse the announcement data
        for item in request_data:
            if item.startswith("TEXT:"):
                text = item.replace("TEXT:", "").strip()
            elif item.startswith("VOICE:"):
                voice_type = item.replace("VOICE:", "").strip()
            elif item.startswith("ID:"):
                request_id = item.replace("ID:", "").strip()
        
        if text:
            announcer.announce(
                "TTS_PROCESSING",
                [
                    f"Converting to speech: '{text[:50]}...'",
                    f"Voice type: {voice_type}",
                    f"Request ID: {request_id}"
                ]
            )
            
            # Generate the audio
            audio_file = self.generate_audio(text, voice_type)
            
            if audio_file:
                # Announce audio is ready
                announcer.announce(
                    "AUDIO_READY",
                    [
                        f"FILE: {audio_file}",
                        f"TEXT: {text}",
                        f"VOICE: {voice_type}",
                        f"ID: {request_id}",
                        "TYPE: WAV audio file"
                    ]
                )
    
    def generate_audio(self, text: str, voice_type: str = "normal") -> str:
        """Generate audio file from text"""
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_wav = f.name
            
            # Choose TTS method based on voice type
            # Default: medium-fast speed (175), normal pitch (50), slight gaps for clarity
            base_args = ['espeak', '-w', temp_wav, '-s', '175', '-p', '50', '-g', '2']
            
            if voice_type == "robot":
                # Slightly slower for robotic effect, lower pitch
                subprocess.run([
                    'espeak', '-w', temp_wav, 
                    '-s', '160',  # Speed
                    '-p', '35',   # Pitch
                    '-g', '5',    # Gap between words
                    text
                ], check=False)
            elif voice_type == "excited":
                # Faster and slightly higher pitch for excitement
                subprocess.run([
                    'espeak', '-w', temp_wav,
                    '-s', '190', '-p', '60', '-g', '1',
                    text
                ], check=False)
            elif voice_type == "serious":
                # Slower and lower pitch for serious topics
                subprocess.run([
                    'espeak', '-w', temp_wav,
                    '-s', '150', '-p', '40', '-g', '3',
                    text
                ], check=False)
            else:
                # Normal voice - optimized for clear, engaging communication
                subprocess.run(base_args + [text], check=False)
            
            announcer.announce(
                "TTS_COMPLETE",
                [
                    f"Generated: {temp_wav}",
                    f"Voice: {voice_type}",
                    f"Text length: {len(text)} chars"
                ]
            )
            
            return temp_wav
            
        except Exception as e:
            announcer.announce(
                "TTS_ERROR",
                [f"TTS generation failed: {e}"]
            )
            return None
    
    def tell(self, format: str = "brief") -> str:
        """Polymorphic tell method"""
        if format == "brief":
            return "PolymorphicTTSService: Converts text to speech via announcements"
        elif format == "full":
            return "I listen for TEXT_TO_SPEECH announcements and generate audio files, then announce AUDIO_READY"
        return str(self)
    
    def ask(self, question: str) -> Any:
        """Polymorphic ask method"""
        if "voices" in question.lower():
            return ["normal", "robot", "excited", "serious"]
        elif "capabilities" in question.lower():
            return "I convert text to speech and announce when ready"
        return None
    
    def do(self, action: str, **kwargs) -> Any:
        """Polymorphic do method"""
        if action == "convert":
            text = kwargs.get('text', '')
            voice = kwargs.get('voice', 'normal')
            return self.generate_audio(text, voice)
        elif action == "announce_ready":
            # Direct announcement (for testing)
            announcer.announce("TEXT_TO_SPEECH", kwargs.get('data', []))
        return None

# Create global instance
tts_service = PolymorphicTTSService()

# Register as discoverable
register_capability('tts', lambda: tts_service)

announcer.announce(
    "PolymorphicTTSService",
    [
        "TTS Service initialized and listening!",
        "Announce TEXT_TO_SPEECH and I'll convert it",
        "I'll announce AUDIO_READY when complete"
    ]
)