#!/usr/bin/env python3
"""
bonjour_discord.py - Minimal Discord capability that announces itself
Just receives messages and announces them. That's it.
Self-manages Discord bot processes.
"""

import discord
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')

from polymorphic_core import announcer, register_capability

try:
    from polymorphic_core.process_management import BaseProcessManager
except ImportError:
    BaseProcessManager = object

# Import voice services - they self-register via Bonjour
from polymorphic_core.audio import (
    PolymorphicAudioPlayer,
    PolymorphicTTSService,
    PolymorphicTranscription
)
# import transcription_to_claude_bridge  # Not needed for basic Discord

# Instantiate to trigger bonjour registration
_ = PolymorphicAudioPlayer()
_ = PolymorphicTTSService()
_ = PolymorphicTranscription()

class DiscordProcessManager(BaseProcessManager):
    """Process manager for Discord bot"""
    
    SERVICE_NAME = "Discord"
    PROCESSES = ['bonjour_discord.py']
    PORTS = []  # Discord uses WebSocket, no specific ports

class BonjourDiscord:
    """Minimal Discord capability - just announces messages"""
    
    def __init__(self):
        # Don't check token until we actually need to run
        self.token = None
        
        # Setup minimal Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        # Message handlers - anyone can register
        self.message_handlers = []
        
        # Register with bonjour for status signals
        announcer.register_service('Discord Bot', self)
    
    def handle_signal(self, signal_type: str, data: dict = None):
        """Handle bonjour signals"""
        if signal_type == 'status':
            return {
                'status': 'running' if self.client.is_ready() else 'connecting',
                'connected': self.client.is_ready(),
                'guilds': len(self.client.guilds) if self.client.is_ready() else 0,
                'latency': f'{self.client.latency * 1000:.2f}ms' if self.client.is_ready() else 'N/A'
            }
        elif signal_type == 'ping':
            return 'pong'
        elif signal_type == 'info':
            return {
                'service': 'Discord Bot',
                'bot_name': 'try-hard#8718',
                'features': ['voice', 'text', 'bonjour']
            }
        else:
            return f'Unknown signal: {signal_type}'
        
        # Announce ourselves
        announcer.announce(
            "BonjourDiscord",
            [
                "I connect to Discord",
                "I receive messages and announce them",
                "Register handlers with me to process messages",
                "I don't do business logic - I just forward messages"
            ]
        )
        
        # Setup Discord handlers
        @self.client.event
        async def on_ready():
            announcer.announce(
                "DISCORD_READY",
                [f"Connected as {self.client.user}"]
            )
            print(f"✅ Discord connected as {self.client.user}")
            
            # Auto-join #general voice channel
            await self.auto_join_voice()
        
        @self.client.event
        async def on_message(message):
            if message.author.bot:
                return
            
            # Announce the message
            announcer.announce(
                "DISCORD_MESSAGE",
                [
                    f"From: {message.author}",
                    f"Content: {message.content}",
                    f"Channel: {message.channel}"
                ]
            )
            
            # Let registered handlers process it
            for handler in self.message_handlers:
                try:
                    response = await handler(message)
                    if response:
                        await message.channel.send(response)
                        break  # First handler that responds wins
                except Exception as e:
                    print(f"Handler error: {e}")
    
    async def auto_join_voice(self):
        """Polymorphically join any voice channel named general"""
        for guild in self.client.guilds:
            for channel in guild.voice_channels:
                if 'general' in channel.name.lower():
                    try:
                        await channel.connect()
                        announcer.announce(
                            "DISCORD_VOICE_JOINED",
                            [
                                f"Joined voice: {channel.name}",
                                f"Guild: {guild.name}",
                                "Ready for voice polymorphism"
                            ]
                        )
                        print(f"🎤 Joined {channel.name} voice")
                        return
                    except Exception as e:
                        print(f"Could not join {channel.name}: {e}")
    
    def register_handler(self, handler):
        """Register a message handler"""
        self.message_handlers.append(handler)
        announcer.announce(
            "BonjourDiscord",
            [f"Registered handler: {handler.__name__}"]
        )
    
    async def run(self):
        """Run the Discord bot"""
        # Only check token when actually starting
        if not self.token:
            self.token = os.getenv('DISCORD_BOT_TOKEN')
            if not self.token:
                raise ValueError("No Discord token found in environment! Set DISCORD_BOT_TOKEN")
        
        await self.client.start(self.token)

# Global instance
_discord = None

def get_discord():
    """Get or create Discord instance"""
    global _discord
    if _discord is None:
        _discord = BonjourDiscord()
    return _discord

# Register as discoverable capability
register_capability("discord", get_discord)

# Create global process manager instance to announce capabilities
if BaseProcessManager != object:  # Only if we have the real class
    _discord_process_manager = DiscordProcessManager()

# Simple message handler for testing
async def echo_handler(message):
    """Simple echo handler"""
    if message.content.startswith('!echo'):
        return f"Echo: {message.content[5:]}"
    return None

# Tournament query handler
async def tournament_handler(message):
    """Handle tournament queries using polymorphic queries"""
    try:
        from polymorphic_queries import query
        
        # Process any message that's not a command
        if not message.content.startswith('!'):
            result = query(message.content)
            if result:
                return result
    except Exception as e:
        print(f"Query error: {e}")
        return f"Sorry, I had trouble processing that: {e}"
    return None

# Main entry point
async def main():
    discord = get_discord()
    discord.register_handler(echo_handler)
    discord.register_handler(tournament_handler)
    
    # Announce we're starting
    announcer.announce(
        "BonjourDiscord",
        ["Starting Discord bot..."]
    )
    
    await discord.run()

if __name__ == "__main__":
    asyncio.run(main())