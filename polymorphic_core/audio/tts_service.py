#!/usr/bin/env python3
"""
polymorphic_tts_service.py - Pure Streaming TTS Service
Converts text to audio and streams directly to mixer - NO FILE CREATION
"""

import subprocess
import io
from typing import Dict, Any
from polymorphic_core import announcer
from polymorphic_core import register_capability

class PolymorphicTTSService:
    """Pure streaming TTS service - no file creation, direct mixer output"""
    
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
        
        self.start_listening()
        
        # Announce our streaming capabilities
        announcer.announce(
            "PolymorphicTTSService",
            [
                "Stream text-to-speech directly to mixer",
                "No file creation - pure streaming audio",
                "Multiple voice types (normal, robot, excited)", 
                "Real-time audio synthesis",
                "Integrates with BonjourAudioMixer"
            ],
            [
                "Listens for TEXT_TO_SPEECH announcements",
                "Streams audio directly to mixer via AUDIO_STREAM",
                "Use: announce('TEXT_TO_SPEECH', ['Hello world', 'normal'])"
            ]
        )
    
    def start_listening(self):
        """Hook into announcements to listen for TEXT_TO_SPEECH"""
        def announcement_listener(service_name: str, capabilities: list, examples: list = None):
            # Listen for TEXT_TO_SPEECH announcements
            if service_name == "TEXT_TO_SPEECH":
                self.on_tts_request(capabilities)
        
        # Register as a listener
        announcer.add_listener(announcement_listener)
        print(f"🔊 [DEBUG] TTS registered listener. Total listeners: {len(announcer.listeners)}")
    
    def on_tts_request(self, request_data: list):
        """Process TTS request and stream to mixer"""
        text = None
        voice_type = "normal"
        request_id = "tts_request"
        
        # Parse request data
        for item in request_data:
            if item.startswith("TEXT:"):
                text = item[5:].strip()
            elif item.startswith("VOICE:"):
                voice_type = item[6:].strip().lower()
            elif item.startswith("ID:"):
                request_id = item[3:].strip()
        
        # If no structured data, assume first item is text
        if not text and request_data:
            text = request_data[0]
            if len(request_data) > 1:
                voice_type = request_data[1]
        
        if text:
            print(f"🔊 [TTS] Streaming: '{text}' (voice: {voice_type})")
            audio_stream = self.generate_audio_stream(text, voice_type)
            
            if audio_stream:
                # Stream directly to mixer
                announcer.announce(
                    "AUDIO_STREAM",
                    [
                        f"TEXT: {text}",
                        f"VOICE: {voice_type}",
                        f"ID: {request_id}",
                        "TYPE: Real-time audio stream",
                        "TARGET: BonjourAudioMixer"
                    ]
                )
                
                # Send the actual audio data to mixer
                announcer.announce(
                    "MIXER_AUDIO_DATA",
                    [
                        f"STREAM_DATA: {audio_stream}",
                        f"FORMAT: WAV",
                        f"SOURCE: TTS",
                        f"ID: {request_id}"
                    ]
                )
    
    def generate_audio_stream(self, text: str, voice_type: str = "normal") -> bytes:
        """Generate audio stream directly - no file creation"""
        try:
            # Choose TTS parameters based on voice type
            if voice_type == "robot":
                cmd = ['espeak', '-s', '160', '-p', '35', '-g', '5', '--stdout', text]
            elif voice_type == "excited":
                cmd = ['espeak', '-s', '190', '-p', '60', '-g', '1', '--stdout', text] 
            elif voice_type == "calm":
                cmd = ['espeak', '-s', '150', '-p', '40', '-g', '3', '--stdout', text]
            else:  # normal
                cmd = ['espeak', '-s', '175', '-p', '50', '-g', '2', '--stdout', text]
            
            # Execute espeak and capture stdout as audio stream
            result = subprocess.run(cmd, capture_output=True, check=False)
            
            if result.returncode == 0 and result.stdout:
                print(f"🔊 [TTS] Generated {len(result.stdout)} bytes of audio")
                return result.stdout
            else:
                print(f"🔊 [TTS] Error: {result.stderr.decode() if result.stderr else 'Unknown error'}")
                return b''
                
        except Exception as e:
            print(f"🔊 [TTS] Exception: {e}")
            return b''
    
    def ask(self, query: str) -> Any:
        """Handle queries about TTS service"""
        query_lower = query.lower().strip()
        
        if query_lower in ['status', 'info']:
            return {
                'service': 'PolymorphicTTSService',
                'mode': 'streaming',
                'file_creation': False,
                'voices': ['normal', 'robot', 'excited', 'calm'],
                'output': 'direct_to_mixer'
            }
        elif query_lower in ['voices', 'voice types']:
            return ['normal', 'robot', 'excited', 'calm']
        elif query_lower.startswith('speak '):
            # Direct TTS request
            text = query[6:]
            self.on_tts_request([f"TEXT: {text}", "VOICE: normal"])
            return f"Speaking: {text}"
        else:
            return "TTS Service - use 'status', 'voices', or 'speak <text>'"
    
    def tell(self, format: str, data: Any = None) -> str:
        """Format TTS service information"""
        if data is None:
            data = self.ask('status')
        
        if format.lower() == 'json':
            import json
            return json.dumps(data, indent=2)
        else:
            return str(data)
    
    def do(self, action: str) -> Any:
        """Perform TTS actions"""
        action_lower = action.lower().strip()
        
        if action_lower.startswith('speak '):
            text = action[6:]
            self.on_tts_request([f"TEXT: {text}", "VOICE: normal"])
            return f"Streaming: {text}"
        elif action_lower.startswith('robot '):
            text = action[6:]
            self.on_tts_request([f"TEXT: {text}", "VOICE: robot"])
            return f"Robot voice: {text}"
        else:
            return "Use 'speak <text>' or 'robot <text>'"

# Global instance
_tts_service = PolymorphicTTSService()

# Register as discoverable capability
register_capability("tts", lambda: _tts_service)

if __name__ == "__main__":
    # Test the streaming TTS
    tts = PolymorphicTTSService()
    
    # Test direct streaming
    print("Testing streaming TTS...")
    tts.on_tts_request(["Hello, this is a test of streaming TTS", "normal"])