#!/usr/bin/env python3
"""
bonjour_discord.py - Minimal Discord capability that announces itself
Just receives messages and announces them. That's it.
"""

import discord
import asyncio
import os
from pathlib import Path
from capability_announcer import announcer
from capability_discovery import register_capability

# Import voice services - they self-register via Bonjour
from polymorphic_core.audio import (
    PolymorphicAudioPlayer,
    PolymorphicTTSService,
    PolymorphicTranscription
)
import transcription_to_claude_bridge

# Instantiate to trigger bonjour registration
_ = PolymorphicAudioPlayer()
_ = PolymorphicTTSService()
_ = PolymorphicTranscription()

class BonjourDiscord:
    """Minimal Discord capability - just announces messages"""
    
    def __init__(self):
        # Load token
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        if not self.token:
            env_file = Path(__file__).parent / '.env'
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('DISCORD_BOT_TOKEN='):
                            self.token = line.split('=', 1)[1].strip().strip('"').strip("'")
                            break
        
        if not self.token:
            raise ValueError("No Discord token found!")
        
        # Setup minimal Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        # Message handlers - anyone can register
        self.message_handlers = []
        
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

# Simple message handler for testing
async def echo_handler(message):
    """Simple echo handler"""
    if message.content.startswith('!echo'):
        return f"Echo: {message.content[5:]}"
    return None

# Main entry point
async def main():
    discord = get_discord()
    discord.register_handler(echo_handler)
    
    # Announce we're starting
    announcer.announce(
        "BonjourDiscord",
        ["Starting Discord bot..."]
    )
    
    await discord.run()

if __name__ == "__main__":
    asyncio.run(main())