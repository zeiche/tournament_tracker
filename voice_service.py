#!/usr/bin/env python3
"""
voice_service.py - Standalone voice service that announces its capabilities
Any module can discover and use voice capabilities through this service
"""

import asyncio
import discord
import os
from pathlib import Path
from typing import Optional, Dict, Any
from capability_announcer import announcer
from capability_discovery import discover_capability

class VoiceService:
    """Standalone voice service that can be discovered and used by any module"""
    
    _instance = None
    _voice_clients: Dict[int, discord.VoiceClient] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Announce our capabilities
        announcer.announce(
            "VoiceService",
            [
                "I provide voice channel connectivity",
                "I can join any voice channel",
                "I can speak using TTS",
                "I can play audio files",
                "I can be discovered by any module",
                "I maintain voice connections for multiple guilds",
                "Methods: join_channel, join_user_channel, leave_channel, speak, play_audio",
                "Example: voice = discover_capability('voice')"
            ]
        )
        
        self.voice_clients = {}
        self.bot_client = None
        
    async def initialize_with_client(self, bot_client: discord.Client):
        """Initialize with a Discord client (called by whoever needs voice)"""
        self.bot_client = bot_client
        announcer.announce(
            "VoiceService",
            [f"Initialized with Discord client: {bot_client.user}"]
        )
        
    async def join_channel(self, guild_id: int, channel_name: str) -> bool:
        """Join a specific voice channel by name"""
        if not self.bot_client:
            announcer.announce("VoiceService", ["ERROR: No Discord client initialized"])
            return False
            
        guild = self.bot_client.get_guild(guild_id)
        if not guild:
            announcer.announce("VoiceService", [f"Guild {guild_id} not found"])
            return False
            
        # Find the channel
        channel = discord.utils.get(guild.voice_channels, name=channel_name)
        if not channel:
            # Try case-insensitive search
            for vc in guild.voice_channels:
                if vc.name.lower() == channel_name.lower():
                    channel = vc
                    break
                    
        if not channel:
            announcer.announce("VoiceService", [f"Voice channel '{channel_name}' not found"])
            return False
            
        try:
            # Check if already connected in this guild
            if guild_id in self.voice_clients:
                await self.voice_clients[guild_id].move_to(channel)
                announcer.announce("VoiceService", [f"Moved to #{channel.name}"])
            else:
                voice_client = await channel.connect()
                self.voice_clients[guild_id] = voice_client
                announcer.announce("VoiceService", [f"Connected to #{channel.name}"])
            return True
        except Exception as e:
            announcer.announce("VoiceService", [f"Failed to join channel: {e}"])
            return False
            
    async def join_user_channel(self, guild_id: int, user_id: int) -> bool:
        """Join the voice channel a user is currently in"""
        if not self.bot_client:
            return False
            
        guild = self.bot_client.get_guild(guild_id)
        if not guild:
            return False
            
        member = guild.get_member(user_id)
        if not member or not member.voice:
            announcer.announce("VoiceService", [f"User {user_id} not in voice channel"])
            return False
            
        channel = member.voice.channel
        try:
            if guild_id in self.voice_clients:
                await self.voice_clients[guild_id].move_to(channel)
            else:
                voice_client = await channel.connect()
                self.voice_clients[guild_id] = voice_client
            announcer.announce("VoiceService", [f"Joined {member.name}'s channel: #{channel.name}"])
            return True
        except Exception as e:
            announcer.announce("VoiceService", [f"Failed to join user's channel: {e}"])
            return False
            
    async def leave_channel(self, guild_id: int) -> bool:
        """Leave voice channel in a guild"""
        if guild_id in self.voice_clients:
            try:
                await self.voice_clients[guild_id].disconnect()
                del self.voice_clients[guild_id]
                announcer.announce("VoiceService", [f"Left voice channel in guild {guild_id}"])
                return True
            except Exception as e:
                announcer.announce("VoiceService", [f"Error leaving channel: {e}"])
                return False
        return False
        
    async def speak(self, guild_id: int, text: str, voice_type: str = "default") -> bool:
        """Speak text in the voice channel using TTS"""
        if guild_id not in self.voice_clients:
            announcer.announce("VoiceService", ["Not connected to voice in this guild"])
            return False
            
        voice_client = self.voice_clients[guild_id]
        if not voice_client.is_connected():
            announcer.announce("VoiceService", ["Voice client disconnected"])
            del self.voice_clients[guild_id]
            return False
            
        announcer.announce("VoiceService", [f"Speaking: '{text}' with voice '{voice_type}'"])
        
        try:
            # Generate TTS audio
            import subprocess
            import tempfile
            
            temp_wav = tempfile.mktemp(suffix='.wav')
            
            # Use espeak for TTS (available on most Linux systems)
            subprocess.run([
                'espeak',
                '-w', temp_wav,
                '-s', '150',  # Speed
                '-p', '50',   # Pitch  
                text
            ], check=True, capture_output=True)
            
            # Play the audio
            audio_source = discord.FFmpegPCMAudio(temp_wav)
            voice_client.play(
                audio_source,
                after=lambda e: announcer.announce("VoiceService", [f"Playback error: {e}"]) if e else None
            )
            
            # Wait for playback to complete
            while voice_client.is_playing():
                await asyncio.sleep(0.5)
            
            # Clean up
            import os
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
                
            announcer.announce("VoiceService", [f"Finished speaking: '{text}'"])
            return True
            
        except subprocess.CalledProcessError as e:
            announcer.announce("VoiceService", [f"TTS generation failed: {e}"])
            return False
        except Exception as e:
            announcer.announce("VoiceService", [f"Error speaking: {e}"])
            return False
        
    async def play_audio(self, guild_id: int, audio_file: str) -> bool:
        """Play an audio file in the voice channel"""
        if guild_id not in self.voice_clients:
            return False
            
        voice_client = self.voice_clients[guild_id]
        if not voice_client.is_connected():
            del self.voice_clients[guild_id]
            return False
            
        try:
            if not os.path.exists(audio_file):
                announcer.announce("VoiceService", [f"Audio file not found: {audio_file}"])
                return False
                
            # Play the audio
            audio_source = discord.FFmpegPCMAudio(audio_file)
            voice_client.play(
                audio_source,
                after=lambda e: announcer.announce("VoiceService", [f"Playback error: {e}"]) if e else None
            )
            
            # Wait for playback to complete
            while voice_client.is_playing():
                await asyncio.sleep(0.5)
                
            announcer.announce("VoiceService", [f"Finished playing: {audio_file}"])
            return True
        except Exception as e:
            announcer.announce("VoiceService", [f"Error playing audio: {e}"])
            return False
            
    def is_connected(self, guild_id: int) -> bool:
        """Check if connected to voice in a guild"""
        if guild_id in self.voice_clients:
            return self.voice_clients[guild_id].is_connected()
        return False
        
    def get_current_channel(self, guild_id: int) -> Optional[str]:
        """Get the name of the current voice channel in a guild"""
        if guild_id in self.voice_clients:
            vc = self.voice_clients[guild_id]
            if vc.is_connected() and vc.channel:
                return vc.channel.name
        return None
        
    async def announce_in_all_channels(self, message: str):
        """Announce a message in all connected voice channels"""
        for guild_id in list(self.voice_clients.keys()):
            await self.speak(guild_id, message)
            
    def get_status(self) -> Dict[str, Any]:
        """Get current status of voice connections"""
        status = {
            "connected_guilds": len(self.voice_clients),
            "connections": {}
        }
        
        for guild_id, vc in self.voice_clients.items():
            if vc.is_connected():
                status["connections"][guild_id] = {
                    "channel": vc.channel.name if vc.channel else "Unknown",
                    "members": len(vc.channel.members) if vc.channel else 0
                }
                
        return status

# Global instance that can be discovered
_voice_service_instance = VoiceService()

def get_voice_service():
    """Get the global voice service instance"""
    return _voice_service_instance

# Register with capability discovery
def register_voice_capability():
    """Register voice service for discovery"""
    try:
        from capability_discovery import register_capability
        register_capability("voice", get_voice_service)
        announcer.announce("VoiceService", ["Registered as discoverable capability"])
    except ImportError:
        # Discovery module not available yet
        pass

# Auto-register when imported
register_voice_capability()