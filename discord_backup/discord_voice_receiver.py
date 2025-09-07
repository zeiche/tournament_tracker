#!/usr/bin/env python3
"""
discord_voice_receiver.py - Receives Discord voice and announces it via Bonjour
When Discord receives audio, it announces for any listening services
"""

import discord
from typing import Optional
from capability_announcer import announcer
from capability_discovery import register_capability, discover_capability

class DiscordVoiceReceiver:
    """Receives Discord voice and announces it to the system"""
    
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
            "DiscordVoiceReceiver",
            [
                "I receive audio from Discord voice channels",
                "I announce when users speak",
                "I broadcast voice events to the system",
                "Any service can listen for my announcements",
                "Events: user_speaking, user_stopped_speaking, audio_received"
            ]
        )
        
        self.listeners = []
        self.voice_clients = {}
        
    def on_user_speaking(self, user_id: int, guild_id: int, speaking: bool):
        """Called when a user starts/stops speaking"""
        if speaking:
            announcer.announce(
                "DISCORD_VOICE",
                [
                    f"USER_SPEAKING: {user_id}",
                    f"GUILD: {guild_id}",
                    "STATUS: Started speaking"
                ]
            )
        else:
            announcer.announce(
                "DISCORD_VOICE",
                [
                    f"USER_STOPPED_SPEAKING: {user_id}",
                    f"GUILD: {guild_id}",
                    "STATUS: Stopped speaking"
                ]
            )
    
    def on_audio_received(self, user_id: int, guild_id: int, audio_data: bytes):
        """Called when audio data is received"""
        announcer.announce(
            "DISCORD_AUDIO",
            [
                f"AUDIO_RECEIVED: {len(audio_data)} bytes",
                f"USER: {user_id}",
                f"GUILD: {guild_id}",
                "TYPE: Raw audio data"
            ]
        )
        
        # Broadcast to any listening services
        for listener in self.listeners:
            try:
                listener(user_id, guild_id, audio_data)
            except Exception as e:
                announcer.announce(
                    "DiscordVoiceReceiver",
                    [f"Listener error: {e}"]
                )
    
    def register_listener(self, callback):
        """Register a callback to receive audio events"""
        self.listeners.append(callback)
        announcer.announce(
            "DiscordVoiceReceiver",
            [f"New listener registered. Total listeners: {len(self.listeners)}"]
        )
        
    def setup_voice_client(self, voice_client: discord.VoiceClient, guild_id: int):
        """Setup voice client to receive audio"""
        self.voice_clients[guild_id] = voice_client
        
        announcer.announce(
            "DiscordVoiceReceiver",
            [
                f"Voice client setup for guild {guild_id}",
                "Ready to receive audio",
                "Starting audio recording..."
            ]
        )
        
        # Start recording with audio sink
        try:
            from discord_audio_sink import get_audio_sink
            
            # Get audio sink
            sink = get_audio_sink(guild_id)
            
            # Define callback for when recording finishes
            async def recording_finished(sink):
                announcer.announce(
                    "RECORDING_FINISHED",
                    [f"Recording completed for guild {guild_id}"]
                )
            
            sink.polymorphic_sink.finished_callback = recording_finished
            
            # Get async service
            async_service = discover_capability('async')
            if not async_service:
                # Fallback to direct import if needed
                import asyncio
                create_task = asyncio.create_task
            else:
                create_task = async_service.create_task
            
            # Start recording
            voice_client.start_recording(
                sink,
                lambda sink, *args: create_task(recording_finished(sink))
            )
            
            announcer.announce(
                "RECORDING_STARTED",
                [
                    f"Voice recording active in guild {guild_id}",
                    "Capturing all voice data",
                    "Say 'Hey Claude' to interact"
                ]
            )
        except Exception as e:
            announcer.announce(
                "RECORDING_ERROR",
                [f"Could not start recording: {e}"]
            )
        
        # Track voice state changes
        @voice_client.client.event
        async def on_voice_state_update(member, before, after):
            """Track when users join/leave/mute/unmute"""
            if after.channel and after.channel == voice_client.channel:
                if after.self_mute != before.self_mute:
                    announcer.announce(
                        "DISCORD_VOICE_STATE",
                        [
                            f"USER: {member.name} ({member.id})",
                            f"MUTED: {after.self_mute}",
                            f"CHANNEL: {after.channel.name}"
                        ]
                    )
                    
                    # If unmuted, announce they might be speaking
                    if not after.self_mute:
                        announcer.announce(
                            "VOICE_READY",
                            [
                                f"User {member.name} unmuted",
                                "Ready to receive voice",
                                "Use !voice <message> to simulate"
                            ]
                        )
                
                # When someone joins voice channel
                if after.channel and not before.channel:
                    announcer.announce(
                        "VOICE_USER_JOINED",
                        [
                            f"USER: {member.name}",
                            f"CHANNEL: {after.channel.name}",
                            "New participant in voice"
                        ]
                    )
    
    def simulate_voice_received(self, user_id: int, guild_id: int, text: str):
        """Simulate receiving voice (for testing without actual audio)"""
        announcer.announce(
            "DISCORD_VOICE_SIMULATED",
            [
                f"SIMULATED_VOICE: '{text}'",
                f"USER: {user_id}",
                f"GUILD: {guild_id}",
                "TYPE: Text simulation of voice"
            ]
        )
        
        # Most Bonjour way: Just announce we have audio!
        # Let whoever wants it discover and take it
        audio_provider = discover_capability('audio_provider')
        if audio_provider:
            audio_provider.provide_simulated_audio(text)
        else:
            # Fallback: announce directly
            announcer.announce(
                "AUDIO_AVAILABLE",
                [
                    f"SOURCE: Discord user {user_id}",
                    f"CONTENT: '{text}'",
                    "TYPE: Simulated voice",
                    "ANYONE can process this!"
                ]
            )

# Global instance
_voice_receiver_instance = DiscordVoiceReceiver()

def get_voice_receiver():
    """Get the global voice receiver instance"""
    return _voice_receiver_instance

# Register with capability discovery
try:
    register_capability("discord_voice_receiver", get_voice_receiver)
    announcer.announce("DiscordVoiceReceiver", ["Registered as discoverable capability"])
except ImportError:
    pass