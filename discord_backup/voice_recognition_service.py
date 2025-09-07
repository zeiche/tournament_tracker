#!/usr/bin/env python3
"""
voice_recognition_service.py - Capture and transcribe voice from Discord
Uses discord.py's voice receiving capabilities with speech recognition
"""

import discord
import asyncio
import wave
import tempfile
import subprocess
import os
from typing import Optional, Dict, Any
from capability_announcer import announcer
from capability_discovery import register_capability

class VoiceRecognitionService:
    """Service that listens to Discord voice and transcribes speech"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce capabilities
        announcer.announce(
            "VoiceRecognitionService",
            [
                "I can listen to voice channels",
                "I transcribe speech to text",
                "I use OpenAI Whisper for transcription",
                "I integrate with Discord voice",
                "Methods: start_listening, stop_listening, transcribe_audio"
            ]
        )
        
        self.is_listening = {}
        self.voice_clients = {}
        self.audio_buffers = {}
        
    async def start_listening(self, voice_client: discord.VoiceClient, guild_id: int):
        """Start listening to a voice channel"""
        if guild_id in self.is_listening and self.is_listening[guild_id]:
            announcer.announce("VoiceRecognition", ["Already listening to this channel"])
            return
            
        self.voice_clients[guild_id] = voice_client
        self.is_listening[guild_id] = True
        self.audio_buffers[guild_id] = []
        
        # Note: discord.py's voice receiving requires special setup
        # For now, we'll use a simpler approach with periodic recording
        announcer.announce(
            "VoiceRecognition", 
            ["Voice receiving requires discord.py[voice] with PyNaCl. Using command-based approach for now."]
        )
        announcer.announce("VoiceRecognition", [f"Started listening in guild {guild_id}"])
        
    async def stop_listening(self, guild_id: int):
        """Stop listening to a voice channel"""
        if guild_id not in self.is_listening or not self.is_listening[guild_id]:
            return False
            
        if guild_id in self.voice_clients:
            vc = self.voice_clients[guild_id]
            if vc.recording:
                vc.stop_recording()
                
        self.is_listening[guild_id] = False
        announcer.announce("VoiceRecognition", [f"Stopped listening in guild {guild_id}"])
        return True
        
    async def _process_audio(self, sink: discord.sinks.WaveSink, guild_id: int):
        """Process recorded audio and transcribe it"""
        announcer.announce("VoiceRecognition", ["Processing recorded audio..."])
        
        # Process each user's audio
        for user_id, audio in sink.audio_data.items():
            # Save audio to temp file
            temp_wav = tempfile.mktemp(suffix='.wav', prefix=f'discord_voice_{user_id}_')
            
            # Write audio data to file
            with open(temp_wav, 'wb') as f:
                f.write(audio.file.getvalue())
            
            # Transcribe the audio
            text = await self.transcribe_audio(temp_wav)
            
            if text:
                announcer.announce(
                    "VoiceRecognition", 
                    [f"User {user_id} said: '{text}'"]
                )
                
                # Send to Claude for processing
                await self._process_voice_command(guild_id, user_id, text)
            
            # Clean up temp file
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
                
    async def transcribe_audio(self, audio_file: str) -> Optional[str]:
        """
        Transcribe audio file to text using Whisper or speech recognition
        """
        try:
            # First try with Whisper if available
            result = subprocess.run(
                ['whisper', audio_file, '--model', 'base', '--language', 'en'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse Whisper output
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if '-->' in line:
                        # This is a timestamp line, next line is the text
                        continue
                    elif line.strip() and not line.startswith('['):
                        return line.strip()
                        
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # Whisper not available, try with speech_recognition
            announcer.announce("VoiceRecognition", ["Whisper not available, trying alternative"])
            
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                
                with sr.AudioFile(audio_file) as source:
                    audio = recognizer.record(source)
                    text = recognizer.recognize_google(audio)
                    return text
                    
            except ImportError:
                announcer.announce("VoiceRecognition", ["speech_recognition not installed"])
                
                # Last resort: use Google's web speech API via a simple HTTP request
                # Or use espeak in reverse (not really possible)
                # For now, return a placeholder
                announcer.announce(
                    "VoiceRecognition", 
                    ["No speech recognition available. Install whisper or speech_recognition"]
                )
                
        except Exception as e:
            announcer.announce("VoiceRecognition", [f"Transcription error: {e}"])
            
        return None
        
    async def _process_voice_command(self, guild_id: int, user_id: int, text: str):
        """Process a voice command from a user"""
        # Check if this is a command for Claude
        if any(trigger in text.lower() for trigger in ['claude', 'hey claude', 'ok claude']):
            # Remove the trigger word
            command = text.lower().replace('hey claude', '').replace('ok claude', '').replace('claude', '').strip()
            
            announcer.announce(
                "VoiceRecognition",
                [f"Voice command received: '{command}'"]
            )
            
            # Send to Claude for processing via capability discovery
            try:
                from capability_discovery import discover_capability
                
                # Get Claude service
                claude = discover_capability('claude')
                if claude:
                    response = await claude.process_voice_command(command)
                    
                    # Get voice service to speak the response
                    voice = discover_capability('voice')
                    if voice:
                        await voice.speak(guild_id, response)
                        
            except Exception as e:
                announcer.announce("VoiceRecognition", [f"Error processing command: {e}"])
                
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            "listening_channels": len([g for g, l in self.is_listening.items() if l]),
            "guilds": list(self.is_listening.keys())
        }

# Global instance
_voice_recognition_instance = VoiceRecognitionService()

def get_voice_recognition_service():
    """Get the global voice recognition instance"""
    return _voice_recognition_instance

# Register with capability discovery
try:
    register_capability("voice_recognition", get_voice_recognition_service)
    announcer.announce("VoiceRecognitionService", ["Registered as discoverable capability"])
except ImportError:
    pass