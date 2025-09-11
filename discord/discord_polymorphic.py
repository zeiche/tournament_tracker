#!/usr/bin/env python3
"""
discord_polymorphic.py - Polymorphic Discord Bridge

Discord bridge using just 3 methods: ask/tell/do
No more complex message routing - just polymorphic intent understanding.
"""

import discord
import asyncio
import os
import sys
sys.path.insert(0, 'utils')
from universal_polymorphic import PolymorphicBridge
from capability_announcer import announcer
from search.polymorphic_queries import query as pq


class DiscordPolymorphic(PolymorphicBridge):
    """
    Discord bridge with just 3 methods.
    
    Instead of complex message handlers:
    - bridge.ask("connected")       # Check connection
    - bridge.tell("status")         # Get status
    - bridge.do("send message")     # Send message
    """
    
    def __init__(self):
        self.client = discord.Client(intents=discord.Intents.default())
        self.connected = False
        self.channel = None
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        
        # Call parent init
        super().__init__()
        
        # Set up Discord event handlers
        self._setup_handlers()
        
        # Announce ourselves
        announcer.announce(
            "DiscordPolymorphic",
            [
                "I'm a polymorphic Discord bridge",
                "I forward messages to Claude",
                "Use ask/tell/do pattern",
                "bridge.ask('connected')",
                "bridge.do('connect')",
                "bridge.do('send', message='Hello')"
            ]
        )
    
    def _setup_handlers(self):
        """Set up Discord event handlers"""
        
        @self.client.event
        async def on_ready():
            self.connected = True
            print(f'Discord connected as {self.client.user}')
            
            # Find default channel
            for guild in self.client.guilds:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        self.channel = channel
                        break
                if self.channel:
                    break
            
            # Announce connection
            announcer.announce(
                "DISCORD_CONNECTED",
                [
                    f"Connected as {self.client.user}",
                    f"Default channel: {self.channel.name if self.channel else 'None'}"
                ]
            )
        
        @self.client.event
        async def on_message(message):
            # Don't respond to ourselves
            if message.author == self.client.user:
                return
            
            # Announce message received
            announcer.announce(
                "DISCORD_MESSAGE",
                [
                    f"From: {message.author}",
                    f"Content: {message.content}",
                    f"Channel: {message.channel.name}"
                ]
            )
            
            # Process polymorphically - just pass to query system
            response = pq(message.content)
            
            # Send response
            if response:
                await message.channel.send(response)
    
    def _handle_ask(self, question: str, **kwargs):
        """Handle Discord-specific questions"""
        q = str(question).lower()
        
        if 'connected' in q:
            return self.connected
        
        if 'channel' in q:
            return self.channel.name if self.channel else "No channel"
        
        if 'user' in q or 'bot' in q:
            return str(self.client.user) if self.client.user else "Not connected"
        
        if 'guilds' in q or 'servers' in q:
            return [g.name for g in self.client.guilds] if self.connected else []
        
        if 'messages' in q:
            # Would need to implement message history
            return "Message history not implemented"
        
        return super()._handle_ask(question, **kwargs)
    
    def _handle_tell(self, format: str, **kwargs):
        """Tell about Discord status"""
        if format in ['status', 'discord']:
            return {
                'connected': self.connected,
                'user': str(self.client.user) if self.client.user else None,
                'channel': self.channel.name if self.channel else None,
                'guilds': len(self.client.guilds) if self.connected else 0
            }
        
        return super()._handle_tell(format, **kwargs)
    
    def _handle_do(self, action: str, **kwargs):
        """Handle Discord actions"""
        act = str(action).lower()
        
        if 'connect' in act:
            return self._connect()
        
        if 'disconnect' in act:
            return self._disconnect()
        
        if 'send' in act or 'message' in act:
            message = kwargs.get('message', '')
            channel = kwargs.get('channel', self.channel)
            return self._send_message(message, channel)
        
        if 'join' in act and 'voice' in act:
            return self._join_voice(kwargs.get('channel'))
        
        if 'leave' in act and 'voice' in act:
            return self._leave_voice()
        
        return super()._handle_do(action, **kwargs)
    
    def _is_connected(self):
        """Check if connected"""
        return self.connected
    
    def _connect(self):
        """Connect to Discord"""
        if self.connected:
            return "Already connected"
        
        if not self.token:
            return "No Discord token found"
        
        # Run the client in background
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run():
            await self.client.start(self.token)
        
        # Start in background thread
        import threading
        def run_discord():
            loop.run_until_complete(run())
        
        thread = threading.Thread(target=run_discord, daemon=True)
        thread.start()
        
        # Wait a bit for connection
        import time
        time.sleep(3)
        
        return "Connecting to Discord..."
    
    def _disconnect(self):
        """Disconnect from Discord"""
        if not self.connected:
            return "Not connected"
        
        async def close():
            await self.client.close()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(close())
        
        self.connected = False
        return "Disconnected from Discord"
    
    def _send_message(self, message: str, channel=None):
        """Send a message"""
        if not self.connected:
            return "Not connected to Discord"
        
        if not channel:
            channel = self.channel
        
        if not channel:
            return "No channel available"
        
        async def send():
            await channel.send(message)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send())
        
        return f"Sent: {message[:50]}..."
    
    def _join_voice(self, channel_name=None):
        """Join voice channel"""
        if not self.connected:
            return "Not connected to Discord"
        
        # Find voice channel
        voice_channel = None
        for guild in self.client.guilds:
            for channel in guild.voice_channels:
                if not channel_name or channel.name.lower() == channel_name.lower():
                    voice_channel = channel
                    break
            if voice_channel:
                break
        
        if not voice_channel:
            return f"Voice channel not found: {channel_name}"
        
        async def join():
            await voice_channel.connect()
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(join())
            return f"Joined voice: {voice_channel.name}"
        except Exception as e:
            return f"Failed to join voice: {e}"
    
    def _leave_voice(self):
        """Leave voice channel"""
        if not self.connected:
            return "Not connected to Discord"
        
        # Find voice client
        for guild in self.client.guilds:
            if guild.voice_client:
                async def leave():
                    await guild.voice_client.disconnect()
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(leave())
                return "Left voice channel"
        
        return "Not in voice channel"
    
    def _get_capabilities(self):
        """List Discord capabilities"""
        return [
            "ask('connected')",
            "ask('channel')",
            "ask('guilds')",
            "tell('status')",
            "do('connect')",
            "do('disconnect')",
            "do('send', message='...')",
            "do('join voice')",
            "do('leave voice')"
        ]
    
    def run(self):
        """Run the Discord bot"""
        if not self.token:
            print("No Discord token found in environment")
            return
        
        print("Starting polymorphic Discord bridge...")
        self.do("connect")
        
        # Keep running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.do("disconnect")


# Global instance
discord_bridge = DiscordPolymorphic()


if __name__ == "__main__":
    # Run the bridge
    discord_bridge.run()