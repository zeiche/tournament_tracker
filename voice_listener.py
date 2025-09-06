#!/usr/bin/env python3
"""
voice_listener.py - Simple voice command listener for Discord
Uses push-to-talk approach: listens when user says a trigger word
"""

import discord
import asyncio
import os
from typing import Optional
from capability_announcer import announcer
from capability_discovery import register_capability

class VoiceListener:
    """Simplified voice listener that responds to text commands about voice"""
    
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
            "VoiceListener",
            [
                "I simulate voice recognition through text commands",
                "Say '!listen' to start voice mode",
                "Say '!voice <message>' to simulate speaking to Claude",
                "I provide a voice interaction experience",
                "Methods: process_voice_command"
            ]
        )
        
        self.voice_mode = {}
        
    async def process_voice_command(self, guild_id: int, user_id: int, message: str) -> Optional[str]:
        """
        Process a simulated voice command
        """
        announcer.announce("VoiceListener", [f"Processing: '{message}'"])
        
        # Check for Claude triggers
        if any(trigger in message.lower() for trigger in ['claude', 'hey claude', 'ok claude']):
            # Extract the actual command
            command = message.lower()
            for trigger in ['hey claude', 'ok claude', 'claude']:
                command = command.replace(trigger, '').strip()
            
            # Process through Claude
            try:
                from capability_discovery import discover_capability
                
                # Use polymorphic query system
                query_handler = discover_capability('query')
                if not query_handler:
                    from polymorphic_queries import query as pq
                    query_handler = pq
                
                # Get response
                response = query_handler(command)
                
                # Shorten for voice
                if len(response) > 200:
                    # Take first meaningful part
                    lines = response.split('\n')
                    response = '\n'.join(lines[:3])
                    if len(response) > 200:
                        response = response[:200] + "..."
                
                return response
                
            except Exception as e:
                announcer.announce("VoiceListener", [f"Error: {e}"])
                return "Sorry, I couldn't process that command."
        
        return None
    
    def enable_voice_mode(self, guild_id: int, channel_id: int):
        """Enable voice mode for a channel"""
        self.voice_mode[guild_id] = channel_id
        announcer.announce("VoiceListener", [f"Voice mode enabled for guild {guild_id}"])
        
    def disable_voice_mode(self, guild_id: int):
        """Disable voice mode"""
        if guild_id in self.voice_mode:
            del self.voice_mode[guild_id]
        announcer.announce("VoiceListener", [f"Voice mode disabled for guild {guild_id}"])
        
    def is_voice_mode(self, guild_id: int) -> bool:
        """Check if voice mode is active"""
        return guild_id in self.voice_mode

# Global instance
_voice_listener_instance = VoiceListener()

def get_voice_listener():
    """Get the global voice listener instance"""
    return _voice_listener_instance

# Register with capability discovery
try:
    register_capability("voice_listener", get_voice_listener)
    announcer.announce("VoiceListener", ["Registered as discoverable capability"])
except ImportError:
    pass