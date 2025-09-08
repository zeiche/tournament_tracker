#!/usr/bin/env python3
"""
bonjour_discord_polymorphic.py - Discord with just ask/tell/do

Instead of specific methods, uses polymorphic pattern while still announcing via Bonjour.
"""

import discord
import asyncio
import os
from pathlib import Path
import sys
sys.path.insert(0, 'utils')
from universal_polymorphic import PolymorphicBridge
from capability_announcer import announcer
from capability_discovery import register_capability

# Import voice services
from polymorphic_core.audio import (
    PolymorphicAudioPlayer,
    PolymorphicTTSService,
    PolymorphicTranscription
)


class BonjourDiscordPolymorphic(PolymorphicBridge):
    """
    Discord service that announces via Bonjour AND uses ask/tell/do pattern.
    
    Examples:
        discord.ask("connected")           # Check if connected
        discord.ask("current channel")     # Get current channel
        discord.tell("status")             # Get full status
        discord.do("connect")              # Connect to Discord
        discord.do("join voice")           # Join voice channel
        discord.do("send", message="...")  # Send message
    """
    
    def __init__(self):
        # Load token first
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        if not self.token:
            env_file = Path(__file__).parent / '.env'
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('DISCORD_BOT_TOKEN='):
                            self.token = line.split('=', 1)[1].strip().strip('"').strip("'")
                            break
        
        # Setup Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        self.connected = False
        self.current_channel = None
        self.voice_client = None
        
        # Message handlers
        self.message_handlers = []
        
        # Call parent init (this announces via UniversalPolymorphic)
        super().__init__()
        
        # Also announce via Bonjour for backward compatibility
        announcer.announce(
            "BonjourDiscordPolymorphic",
            [
                "I'm Discord with ask/tell/do pattern",
                "I still announce via Bonjour",
                "Use discord.ask('connected')",
                "Use discord.do('join voice')",
                "Use discord.tell('status')",
                "Backward compatible with handlers"
            ]
        )
        
        # Setup Discord event handlers
        self._setup_discord_handlers()
    
    def _setup_discord_handlers(self):
        """Setup Discord event handlers"""
        
        @self.client.event
        async def on_ready():
            self.connected = True
            self.current_channel = self.client.get_channel(
                int(os.getenv('DEFAULT_CHANNEL_ID', '0'))
            ) if os.getenv('DEFAULT_CHANNEL_ID') else None
            
            # Announce connection via Bonjour
            announcer.announce(
                "DISCORD_READY",
                [
                    f"Connected as {self.client.user}",
                    f"Guilds: {len(self.client.guilds)}",
                    "Ready for ask/tell/do commands"
                ]
            )
            
            print(f"✅ Discord connected as {self.client.user}")
            
            # Auto-join voice if configured
            if os.getenv('AUTO_JOIN_VOICE', 'false').lower() == 'true':
                asyncio.create_task(self._auto_join_voice())
        
        @self.client.event
        async def on_message(message):
            if message.author.bot:
                return
            
            # Announce via Bonjour
            announcer.announce(
                "DISCORD_MESSAGE",
                [
                    f"From: {message.author}",
                    f"Content: {message.content}",
                    f"Channel: {message.channel}"
                ]
            )
            
            # Process with handlers
            for handler in self.message_handlers:
                try:
                    response = await handler(message)
                    if response:
                        await message.channel.send(response)
                        break
                except Exception as e:
                    print(f"Handler error: {e}")
    
    def _handle_ask(self, question: str, **kwargs) -> Any:
        """
        Handle Discord-specific questions.
        
        Examples:
            ask("connected")        # Is Discord connected?
            ask("user")            # Bot user info
            ask("guilds")          # List guilds
            ask("channel")         # Current channel
            ask("voice")           # Voice connection status
        """
        q = str(question).lower()
        
        if 'connected' in q:
            return self.connected
        
        if 'user' in q or 'bot' in q:
            return str(self.client.user) if self.client.user else None
        
        if 'guild' in q or 'server' in q:
            return [g.name for g in self.client.guilds] if self.connected else []
        
        if 'channel' in q:
            if 'voice' in q:
                return self.voice_client.channel.name if self.voice_client else None
            return self.current_channel.name if self.current_channel else None
        
        if 'voice' in q:
            return {
                'connected': bool(self.voice_client),
                'channel': self.voice_client.channel.name if self.voice_client else None
            }
        
        if 'handlers' in q:
            return len(self.message_handlers)
        
        return super()._handle_ask(question, **kwargs)
    
    def _handle_tell(self, format: str, **kwargs) -> Any:
        """
        Format Discord information.
        
        Examples:
            tell("status")          # Full status
            tell("json")           # JSON format
            tell("brief")          # Short summary
        """
        if format == "status":
            return {
                'connected': self.connected,
                'user': str(self.client.user) if self.client.user else None,
                'guilds': len(self.client.guilds) if self.connected else 0,
                'channel': self.current_channel.name if self.current_channel else None,
                'voice': self.voice_client.channel.name if self.voice_client else None,
                'handlers': len(self.message_handlers)
            }
        
        if format == "brief":
            if self.connected:
                return f"Connected as {self.client.user}"
            return "Not connected"
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: str, **kwargs) -> Any:
        """
        Perform Discord actions.
        
        Examples:
            do("connect")           # Connect to Discord
            do("disconnect")        # Disconnect
            do("join voice")        # Join voice channel
            do("leave voice")       # Leave voice
            do("send", message="...") # Send message
            do("register", handler=...) # Register handler
        """
        act = str(action).lower()
        
        if 'connect' in act and 'dis' not in act:
            return self._do_connect()
        
        if 'disconnect' in act:
            return self._do_disconnect()
        
        if 'join' in act and 'voice' in act:
            channel_name = kwargs.get('channel', 'General')
            return asyncio.run_coroutine_threadsafe(
                self._join_voice(channel_name),
                self.client.loop
            ).result() if self.connected else "Not connected"
        
        if 'leave' in act and 'voice' in act:
            return asyncio.run_coroutine_threadsafe(
                self._leave_voice(),
                self.client.loop
            ).result() if self.voice_client else "Not in voice"
        
        if 'send' in act:
            message = kwargs.get('message', '')
            channel = kwargs.get('channel', self.current_channel)
            if channel and message:
                asyncio.run_coroutine_threadsafe(
                    channel.send(message),
                    self.client.loop
                )
                return f"Sent: {message[:50]}..."
            return "Need channel and message"
        
        if 'register' in act:
            handler = kwargs.get('handler')
            if handler:
                self.message_handlers.append(handler)
                return f"Registered handler"
            return "No handler provided"
        
        return super()._handle_do(action, **kwargs)
    
    def _do_connect(self):
        """Connect to Discord"""
        if self.connected:
            return "Already connected"
        
        if not self.token:
            return "No Discord token"
        
        # Run in background
        def run_discord():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.client.start(self.token))
        
        import threading
        thread = threading.Thread(target=run_discord, daemon=True)
        thread.start()
        
        # Wait for connection
        import time
        for _ in range(10):
            if self.connected:
                return "Connected to Discord"
            time.sleep(0.5)
        
        return "Connecting..."
    
    def _do_disconnect(self):
        """Disconnect from Discord"""
        if not self.connected:
            return "Not connected"
        
        asyncio.run_coroutine_threadsafe(
            self.client.close(),
            self.client.loop
        )
        self.connected = False
        return "Disconnected"
    
    async def _join_voice(self, channel_name: str = "General"):
        """Join voice channel"""
        for guild in self.client.guilds:
            for channel in guild.voice_channels:
                if channel.name.lower() == channel_name.lower():
                    try:
                        self.voice_client = await channel.connect()
                        
                        # Announce via Bonjour
                        announcer.announce(
                            "DISCORD_VOICE_JOINED",
                            [f"Joined voice channel: {channel.name}"]
                        )
                        
                        return f"Joined {channel.name}"
                    except Exception as e:
                        return f"Failed to join: {e}"
        
        return f"Channel {channel_name} not found"
    
    async def _leave_voice(self):
        """Leave voice channel"""
        if self.voice_client:
            channel_name = self.voice_client.channel.name
            await self.voice_client.disconnect()
            self.voice_client = None
            
            # Announce via Bonjour
            announcer.announce(
                "DISCORD_VOICE_LEFT",
                [f"Left voice channel: {channel_name}"]
            )
            
            return f"Left {channel_name}"
        return "Not in voice"
    
    async def _auto_join_voice(self):
        """Auto-join configured voice channel"""
        channel_name = os.getenv('DEFAULT_VOICE_CHANNEL', 'General')
        result = await self._join_voice(channel_name)
        print(f"Auto-join voice: {result}")
    
    def run(self):
        """Run the Discord bot (backward compatibility)"""
        print("Starting BonjourDiscord with polymorphic pattern...")
        result = self.do("connect")
        print(result)
        
        # Keep running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.do("disconnect")
    
    # Backward compatibility
    def register_handler(self, handler):
        """Legacy method - redirects to do()"""
        return self.do("register", handler=handler)


# For backward compatibility
if __name__ == "__main__":
    discord_bot = BonjourDiscordPolymorphic()
    discord_bot.run()